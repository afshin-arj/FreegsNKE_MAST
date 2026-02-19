from mast_freegsnke.download import BulkDownloader

def test_render_candidates():
    dl = BulkDownloader(s5cmd_path="s5cmd", level2_s3_prefix="s3://B/level2", layout_patterns=[
        "{prefix}/{group}/shot_{shot}.zarr",
        "{prefix}/shot_{shot}/{group}.zarr",
    ])
    c = dl._render_candidates(30201, "pf_active")
    assert c[0].endswith("/pf_active/shot_30201.zarr")
    assert c[1].endswith("/shot_30201/pf_active.zarr")
