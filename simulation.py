"""Campagnes de simulation du VRAI intelligence.py de R.A.L.F. sur ordinateur.

Exemples (Python 3.11+) :
    python simulation.py --count 1000 --profile standard
    python simulation.py --count 10000 --profile stress --seed 2000
    python simulation.py --count 1 --seed 92880 --verbose

Le simulateur remplace uniquement le matériel (URM09, photorésistance, moteur,
servo et horloge) par des doubles. Les décisions restent prises par la classe
Intelligence de production. Les puissances PWM ne donnent pas une vitesse
mesurée : un facteur vitesse/puissance hypothétique est utilisé ici.
"""

import argparse
import contextlib
import csv
import importlib.util
import io
import json
import random
import sys
import tomllib
import types
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PROFILES = {
    "standard": {
        "height_noise_cm": 0.25,
        "height_false_rate": 0.005,
        "height_no_echo_rate": 0.01,
        "brightness_noise_percent": 1.0,
        "brightness_false_rate": 0.005,
    },
    "stress": {
        "height_noise_cm": 0.50,
        "height_false_rate": 0.10,
        "height_no_echo_rate": 0.10,
        "brightness_noise_percent": 2.0,
        "brightness_false_rate": 0.10,
    },
}


@dataclass
class SimParameters:
    initial_height_cm: float = 60.0
    speed_at_100_cm_s: float = 2.0
    marker_half_width_cm: float = 0.6
    cable_brightness: float = 60.0
    black_marker_brightness: float = 20.0
    final_marker_brightness: float = 90.0
    final_marker: str = "bright"
    height_noise_cm: float = 0.25
    height_false_rate: float = 0.005
    height_no_echo_rate: float = 0.01
    brightness_noise_percent: float = 1.0
    brightness_false_rate: float = 0.005

    def validate(self, cfg):
        if self.initial_height_cm <= cfg.START_PROPAGATION_HEIGHT + 2:
            raise ValueError("La hauteur initiale doit être au-dessus du premier repère.")
        if self.speed_at_100_cm_s <= 0 or self.marker_half_width_cm <= 0:
            raise ValueError("La vitesse et la demi-largeur des rubans doivent être positives.")
        for name in ("height_false_rate", "height_no_echo_rate", "brightness_false_rate"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError("{} doit être compris entre 0 et 1.".format(name))
        for name in ("height_noise_cm", "brightness_noise_percent"):
            if getattr(self, name) < 0:
                raise ValueError("{} doit être positif ou nul.".format(name))
        if self.final_marker not in ("bright", "dark", "none"):
            raise ValueError("Troisième repère invalide.")
        if self.initial_height_cm > 320:
            raise ValueError("Hauteur initiale hors de la portée 0–320 cm du logiciel.")


class FakeDistance:
    """Même interface que DFRobot_URM09 utilisée par Intelligence."""

    def __init__(self, env):
        self.env = env

    def get_distance(self):
        e = self.env
        e.readings += 1
        if e.rng.random() < e.sim.height_no_echo_rate:
            e.no_echo += 1
            return -1
        value = e.height + e.rng.gauss(0.0, e.sim.height_noise_cm)
        if e.rng.random() < e.sim.height_false_rate:
            e.distance_outliers += 1
            value += e.rng.choice((-12.0, -8.0, 8.0, 12.0))
        return round(value)


class FakeBrightness:
    """Même interface que Sensor : valeur ADC entière de 0 à 65535."""

    def __init__(self, env):
        self.env = env

    def get_value(self):
        e = self.env
        sim = e.sim
        c = e.cfg
        h = e.height
        if (abs(h - c.START_PROPAGATION_HEIGHT) <= sim.marker_half_width_cm
                or abs(h - c.END_PROPAGATION_HEIGHT) <= sim.marker_half_width_cm):
            brightness = sim.black_marker_brightness
        elif abs(h - c.STOP_PROPAGATION_HEIGHT) <= sim.marker_half_width_cm:
            brightness = {
                "bright": sim.final_marker_brightness,
                "dark": sim.black_marker_brightness,
                "none": sim.cable_brightness,
            }[sim.final_marker]
        else:
            brightness = sim.cable_brightness
        brightness += e.rng.gauss(0.0, sim.brightness_noise_percent)
        if e.rng.random() < sim.brightness_false_rate:
            e.brightness_outliers += 1
            brightness = e.rng.uniform(0, 100)
        brightness = max(0.0, min(100.0, brightness))
        return round(brightness * 65535 / 100)


class SimEnvironment:
    def __init__(self, seed, cfg, sim):
        self.seed = seed
        self.cfg = cfg
        self.sim = sim
        self.rng = random.Random(seed)
        self.height = sim.initial_height_cm
        self.t = 0.0
        self.motor = 0.0
        self.trap = 0.0
        self.events = []
        self.readings = 0
        self.no_echo = 0
        self.distance_outliers = 0
        self.brightness_outliers = 0
        self.distance_sensor = FakeDistance(self)
        self.brightness_sensor = FakeBrightness(self)

    def sleep(self, duration):
        if duration < 0:
            raise ValueError("Durée de simulation négative")
        # Hypothèse simplifiée : vitesse de descente proportionnelle au PWM.
        # Sans inertie, sans patinage, sans loi de freinage ni pente variable.
        speed = self.sim.speed_at_100_cm_s * self.motor / 100
        self.height = max(0.0, self.height - speed * duration)
        self.t += duration

    def event(self, name, value):
        self.events.append((name, value, self.height, self.t))

    def forward(self, power):
        self.motor = power
        self.event("motor", power)

    def stop(self):
        self.motor = 0
        self.event("stop", 0)

    def set_trap(self, angle):
        self.trap = angle
        self.event("trap", angle)
        return True


class Simulator:
    """Charge une seule fois intelligence.py, puis réutilise sa classe réelle."""

    def __init__(self, config):
        self.config = config
        self.current = None
        self.settings = types.SimpleNamespace(**config)

        fake_utils = types.ModuleType("utils")
        fake_utils.settings = self.settings
        fake_utils.DFRobot_URM09 = FakeDistance
        fake_utils.Sensor = FakeBrightness
        fake_utils.AvailableMusics = types.SimpleNamespace(BIRTHDAY=["note"])
        fake_utils.forward = lambda power: self.current.forward(power)
        fake_utils.stop = lambda: self.current.stop()
        fake_utils.set_trapdoor_position = lambda angle: self.current.set_trap(angle)
        fake_utils.play_music = lambda tune: self.current.event("music", tune)
        fake_utils.error_leds_state = lambda: self.current.event("error_leds", None)

        self._old_utils = sys.modules.get("utils")
        sys.modules["utils"] = fake_utils
        try:
            spec = importlib.util.spec_from_file_location("ralf_intelligence_simulation", ROOT / "intelligence.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            if self._old_utils is None:
                sys.modules.pop("utils", None)
            else:
                sys.modules["utils"] = self._old_utils
        module.time = self
        self.engine_module = module

    def monotonic(self):
        return self.current.t

    def sleep(self, duration):
        self.current.sleep(duration)

    def run_one(self, seed, sim, verbose=False):
        sim.validate(self.settings)
        env = SimEnvironment(seed, self.settings, sim)
        self.current = env
        engine = self.engine_module.Intelligence(env.distance_sensor, env.brightness_sensor)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            success = engine.run_intelligence()

        start = end = stop_height = None
        # Événements physiques : trappe ouverte au premier, fermée au deuxième,
        # premier ordre stop au troisième. Le finally ajoute un second stop.
        opened = False
        for kind, value, height, timestamp in env.events:
            if kind == "trap" and value != 0 and start is None:
                start = height
                opened = True
            elif kind == "trap" and value == 0 and opened and end is None:
                end = height
            elif kind == "stop" and stop_height is None:
                stop_height = height

        # Un arrêt d'urgence en cours de mission n'est pas un repère validé.
        if not success:
            stop_height = None
        status = "OK" if success else "EMERGENCY"
        if not success and not any(k == "error_leds" for k, *_ in env.events):
            status = "FAILED"
        target = (self.settings.START_PROPAGATION_HEIGHT,
                  self.settings.END_PROPAGATION_HEIGHT,
                  self.settings.STOP_PROPAGATION_HEIGHT)
        row = {
            "seed": seed, "status": status,
            "start_cm": round(start, 3) if start is not None else "",
            "end_cm": round(end, 3) if end is not None else "",
            "stop_cm": round(stop_height, 3) if stop_height is not None else "",
            "start_error_cm": round(start - target[0], 3) if start is not None else "",
            "end_error_cm": round(end - target[1], 3) if end is not None else "",
            "stop_error_cm": round(stop_height - target[2], 3) if stop_height is not None else "",
            "elapsed_s": round(env.t, 3),
            "readings": env.readings,
            "no_echo": env.no_echo,
            "distance_outliers": env.distance_outliers,
            "brightness_outliers": env.brightness_outliers,
            "final_height_cm": round(env.height, 3),
        }
        if verbose:
            print("--- Simulation seed {} ---".format(seed))
            print("Paramètres PWM : {} / {} / {} %".format(
                self.settings.MOTOR_POWER_BEFORE_RELEASE,
                self.settings.MOTOR_POWER_DURING_RELEASE,
                self.settings.MOTOR_POWER_AFTER_RELEASE))
            print(output.getvalue().strip())
            print("Déroulement des actionneurs :")
            for kind, value, height, timestamp in env.events:
                if kind in ("motor", "trap", "stop", "error_leds"):
                    print("  t={:6.2f}s  h={:6.2f}cm  {:10s} {}".format(timestamp, height, kind, value))
            print("Données :", row)
        return row


FIELDS = (
    "seed", "status", "start_cm", "end_cm", "stop_cm",
    "start_error_cm", "end_error_cm", "stop_error_cm",
    "elapsed_s", "readings", "no_echo", "distance_outliers",
    "brightness_outliers", "final_height_cm",
)


def load_settings(path):
    with path.open("rb") as file:
        return tomllib.load(file)


def build_sim_parameters(args):
    profile = dict(PROFILES[args.profile])
    kwargs = dict(
        initial_height_cm=args.initial_height,
        speed_at_100_cm_s=args.speed,
        marker_half_width_cm=args.marker_half_width,
        final_marker=args.final_marker,
    )
    kwargs.update(profile)
    return SimParameters(**kwargs)


def summarize(rows, config):
    count = len(rows)
    good = [r for r in rows if r["status"] == "OK"]
    def within(r, limit):
        return all(isinstance(r[k], (int, float)) and abs(r[k]) <= limit
                   for k in ("start_error_cm", "end_error_cm", "stop_error_cm"))
    on_marker = None if config.final_marker == "none" else sum(all(
        abs(r[k]) <= config.marker_half_width_cm
        for k in ("start_error_cm", "end_error_cm", "stop_error_cm")
    ) for r in good)
    summary = {
        "count": count,
        "completed": len(good),
        "emergencies": sum(r["status"] == "EMERGENCY" for r in rows),
        "finished_percent": round(len(good) * 100 / count, 4),
        "all_three_within_1cm": sum(within(r, 1) for r in good),
        "all_three_within_2cm": sum(within(r, 2) for r in good),
        "all_three_on_marker": on_marker,
    }
    for metric in ("all_three_within_1cm", "all_three_within_2cm", "all_three_on_marker"):
        summary[metric + "_percent"] = (
            round(100 * summary[metric] / count, 4)
            if summary[metric] is not None else None
        )
    return summary


def run_campaign(count, first_seed, config, sim, *, output=None, verbose=False):
    rows = []
    engine = Simulator(config)
    for index in range(count):
        rows.append(engine.run_one(first_seed + index, sim, verbose=verbose))
    summary = summarize(rows, sim)
    if output is not None:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        meta = {
            "reference": "intelligence.py (imports matériel simulés)",
            "first_seed": first_seed,
            "last_seed": first_seed + count - 1,
            "settings": config,
            "simulator": vars(sim),
            "summary": summary,
        }
        summary_path = output.with_suffix(".summary.json")
        summary_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Campagnes reproductibles R.A.L.F. à trois scotchs (Python PC).")
    parser.add_argument("--count", type=int, default=1000, help="Nombre de descentes (défaut : 1000).")
    parser.add_argument("--seed", type=int, default=0, help="Première seed (défaut : 0).")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="standard")
    parser.add_argument("--speed", type=float, default=2.0, help="Vitesse supposée à 100 %% PWM, en cm/s.")
    parser.add_argument("--initial-height", type=float, default=60.0, help="Hauteur au départ (cm).")
    parser.add_argument("--marker-half-width", type=float, default=0.6, help="Demi-largeur des 3 rubans en cm.")
    parser.add_argument("--final-marker", choices=("bright", "dark", "none"), default="bright")
    parser.add_argument("--settings", type=Path, default=ROOT / "settings.toml", help="Fichier de configuration.")
    parser.add_argument("--output", type=Path, default=None, help="Chemin CSV (défaut : results/...).")
    parser.add_argument("--show-failures", type=int, default=5, help="Nombre de seeds non conformes à afficher.")
    parser.add_argument("--verbose", action="store_true", help="Afficher les actions de chaque descente (éviter pour un grand lot).")
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("--count doit être >= 1")
    if args.show_failures < 0:
        parser.error("--show-failures doit être >= 0")
    cfg = load_settings(args.settings)
    sim = build_sim_parameters(args)
    sim.validate(types.SimpleNamespace(**cfg))
    output = args.output or ROOT / "results" / "simulation_{}_{}_seed{}.csv".format(args.profile, args.count, args.seed)
    rows, summary = run_campaign(args.count, args.seed, cfg, sim, output=output,
                                 verbose=args.verbose)
    print("\n=== R.A.L.F. : {} descentes / profil {} ===".format(args.count, args.profile))
    print("Mission terminée : {} / {} ({} %)".format(summary["completed"], args.count, summary["finished_percent"]))
    print("Arrêts d'urgence : {}".format(summary["emergencies"]))
    print("Trois repères à ±1 cm : {} ({} %)".format(summary["all_three_within_1cm"], summary["all_three_within_1cm_percent"]))
    print("Trois repères à ±2 cm : {} ({} %)".format(summary["all_three_within_2cm"], summary["all_three_within_2cm_percent"]))
    if summary["all_three_on_marker"] is None:
        print("Trois repères sur ruban : sans objet (3e ruban absent)")
    else:
        print("Trois repères sur ruban : {} ({} %)".format(summary["all_three_on_marker"], summary["all_three_on_marker_percent"]))
    bad = [r for r in rows if r["status"] != "OK" or any(
        r[k] == "" or abs(r[k]) > 1 for k in ("start_error_cm", "end_error_cm", "stop_error_cm"))]
    if bad and args.show_failures:
        print("Seeds à rejouer ({} exemples) : {}".format(
            min(args.show_failures, len(bad)), ", ".join(str(r["seed"]) for r in bad[:args.show_failures])))
    print("CSV :", output)
    print("Métadonnées :", output.with_suffix(".summary.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
