from pathlib import Path
import json

from mast_freegsnke.probe_geometry import (
    build_geometry_from_machine_dir,
    smoke_test_geometry,
    write_geometry_templates,
    to_freegsnke_magnetic_probes,
)


def _valid_payload() -> dict:
    return {
        "metadata": {"machine": "TEST", "source": "unit_test", "phi_unit": "deg"},
        "flux_loops": [
            {"name": "FL1", "r_m": 1.0, "z_m": 0.0, "turns": 10, "area_m2": 1e-4, "psi_coupling_factor": None}
        ],
        "pickup_coils": [
            {
                "name": "PC1",
                "r_m": 1.2,
                "phi_deg": 300.0,
                "z_m": 0.1,
                "n_r": 1.0,
                "n_phi": 0.0,
                "n_z": 0.0,
                "effective_area_m2": 2e-4,
                "gain": None,
                "orientation": "PARALLEL",
            }
        ],
    }


def test_probe_geometry_missing_file(tmp_path: Path):
    geom, report = build_geometry_from_machine_dir(machine_dir=tmp_path)
    assert geom is None
    assert report["resolved"] is False
    assert report["errors"]


def test_probe_geometry_json_ok(tmp_path: Path):
    p = tmp_path / "probe_geometry.json"
    p.write_text(json.dumps(_valid_payload(), indent=2))
    geom, report = build_geometry_from_machine_dir(tmp_path)
    assert geom is not None
    assert report["resolved"] is True
    assert report["source"] == "probe_geometry.json"


def test_probe_geometry_python_module_ok(tmp_path: Path):
    # No probe_geometry.json; should fall back to python module
    (tmp_path / "probe_geometry.py").write_text(
        "from mast_freegsnke.probe_geometry import ProbeGeometry, FluxLoop, PickupCoil\n"
        "def build_probe_geometry():\n"
        "    return ProbeGeometry(\n"
        "        flux_loops=[FluxLoop(name='FL1', r_m=1.0, z_m=0.0)],\n"
        "        pickup_coils=[PickupCoil(name='PC1', r_m=1.2, z_m=0.1, phi_deg=300.0, n_r=1.0, n_phi=0.0, n_z=0.0, orientation='PARALLEL')],\n"
        "        metadata={'machine':'TEST','source':'unit_test','phi_unit':'deg'}\n"
        "    )\n"
    )
    geom, report = build_geometry_from_machine_dir(tmp_path)
    assert geom is not None
    assert report["resolved"] is True
    assert str(report["source"]).startswith("python:")


def test_probe_geometry_csv_ok(tmp_path: Path):
    # No probe_geometry.json and no python module; should fall back to csv
    (tmp_path / "flux_loops.csv").write_text("name,r_m,z_m,turns,area_m2,psi_coupling_factor\nFL1,1.0,0.0,,,\n")
    (tmp_path / "pickup_coils.csv").write_text("name,r_m,phi_deg,z_m,n_r,n_phi,n_z,effective_area_m2,gain,orientation\nPC1,1.2,300.0,0.1,1.0,0.0,0.0,,,PARALLEL\n")
    geom, report = build_geometry_from_machine_dir(tmp_path)
    assert geom is not None
    assert report["resolved"] is True
    assert report["source"] == "csv"


def test_probe_geometry_smoke_and_freegsnke_dict(tmp_path: Path):
    p = tmp_path / "probe_geometry.json"
    p.write_text(json.dumps(_valid_payload(), indent=2))
    geom, report = build_geometry_from_machine_dir(tmp_path)
    assert geom is not None
    ok, srep = smoke_test_geometry(geom)
    assert ok is True
    assert srep["n_flux_loops"] == 1
    assert srep["n_pickup_coils"] == 1

    mp = to_freegsnke_magnetic_probes(geom)
    assert "flux_loops" in mp and "pickups" in mp
    assert len(mp["flux_loops"]) == 1
    assert len(mp["pickups"]) == 1


def test_geom_template_writer(tmp_path: Path):
    out = write_geometry_templates(tmp_path)
    assert (tmp_path / "probe_geometry.template.json").exists()
    assert (tmp_path / "flux_loops.template.csv").exists()
    assert (tmp_path / "pickup_coils.template.csv").exists()
    assert "probe_geometry.template.json" in out
