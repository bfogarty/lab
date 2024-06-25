import cdktf

from lab.stacks import Lab


class TestLab:
    def test_terraform_is_valid(self):
        lab_stack = Lab(cdktf.Testing.app(), "lab")
        assert cdktf.Testing.to_be_valid_terraform(cdktf.Testing.full_synth(lab_stack))
