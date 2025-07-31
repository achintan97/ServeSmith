"""Tests for Resource model."""

from servesmith.models.resource import Resource


def test_resource_auto_populates_from_instance_type():
    r = Resource(instance_type="g4dn.xlarge")
    assert r.cpu == 4
    assert r.memory == 16
    assert r.gpu == 1
    assert r.gpu_memory == 16


def test_resource_unknown_instance_type():
    r = Resource(instance_type="x99.mega")
    assert r.cpu is None
    assert r.gpu is None


def test_resource_manual_override():
    r = Resource(instance_type="g4dn.xlarge", cpu=2)
    assert r.cpu == 2  # manual value preserved
    assert r.memory == 16  # auto-populated


def test_is_gpu_instance():
    assert Resource(instance_type="g5.xlarge").is_gpu_instance()
    assert not Resource(instance_type="inf2.xlarge").is_gpu_instance()


def test_is_inferentia_instance():
    assert Resource(instance_type="inf2.48xlarge").is_inferentia_instance()
    assert not Resource(instance_type="g5.xlarge").is_inferentia_instance()
