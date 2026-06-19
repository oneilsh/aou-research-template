from utilities.workspace import discover, render_env


def fake_wb(*args):
    if args[:2] == ("workspace", "describe"):
        return {"googleProjectId": "proj-123"}
    if args[:2] == ("resource", "list"):
        return [
            {"resourceType": "GCS_BUCKET", "id": "workspace-bucket", "bucketName": "wb-main"},
            {"resourceType": "GCS_BUCKET", "id": "temporary-workspace-bucket", "bucketName": "wb-tmp"},
            {"resourceType": "BQ_DATASET", "projectId": "cdr-proj", "datasetId": "R2024"},
        ]
    raise AssertionError(args)


def test_discover_maps_resources():
    out = discover(wb=fake_wb)
    assert out["GOOGLE_CLOUD_PROJECT"] == "proj-123"
    assert out["WORKSPACE_CDR"] == "cdr-proj.R2024"
    assert out["WORKSPACE_BUCKET"] == "gs://wb-main"
    assert out["WORKSPACE_TEMP_BUCKET"] == "gs://wb-tmp"


def test_render_env_is_sourceable():
    text = render_env({"GOOGLE_CLOUD_PROJECT": "p", "WORKSPACE_CDR": "a.b"})
    assert "export GOOGLE_CLOUD_PROJECT='p'" in text
    assert "export WORKSPACE_CDR='a.b'" in text
