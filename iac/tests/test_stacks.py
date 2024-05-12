from cdktf import Testing

from lab.stacks import Lab


class TestLab:
    def test_terraform_is_valid(self):
        lab_stack = Lab(Testing.app(), "lab")
        assert Testing.to_be_valid_terraform(Testing.full_synth(lab_stack))
