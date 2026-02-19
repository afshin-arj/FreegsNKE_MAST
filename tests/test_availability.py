from mast_freegsnke.availability import check_groups

def test_check_groups_ok_and_missing():
    def discover(shot: int, group: str) -> str:
        if group == "pf_active":
            return "s3://bucket/pf_active/shot_1.zarr"
        raise FileNotFoundError("no such group")
    out = check_groups(shot=1, groups=["pf_active","magnetics"], discover=discover)
    assert out["pf_active"].exists is True
    assert out["magnetics"].exists is False
