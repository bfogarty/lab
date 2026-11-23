{
  description = "Homelab infrastructure-as-code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            # Terraform's BUSL license is unfree in nixpkgs.
            config.allowUnfreePredicate = pkg: nixpkgs.lib.getName pkg == "terraform";
          };

          # `cdk8s import` uses jsii-srcmak, which copies jsii dependencies out
          # of the CLI's own package into a temp dir with `fs.copy`. From the
          # read-only store, the copies keep read-only modes, so deleting the
          # temp dir fails with EACCES.
          #
          # Make each copy writable right after it is made. `--replace-fail`
          # stops the build if a version bump changes the patched code.
          chmodWritable =
            target:
            ''require("child_process").execFileSync("${pkgs.coreutils}/bin/chmod", ["-R", "u+w", ${target}])'';

          cdk8s-cli = pkgs.cdk8s-cli.overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              substituteInPlace $out/lib/node_modules/cdk8s-cli/node_modules/jsii-srcmak/lib/compile.js \
                --replace-fail 'await fs.copy(dir, targetdir);' 'await fs.copy(dir, targetdir); ${chmodWritable "targetdir"};'
            '';
          });
        in
        {
          default = pkgs.mkShell {
            packages = [
              # Python project. The cdktn and cdk8s libraries run on Node
              # through jsii.
              pkgs.python314
              # Build Poetry on the same Python. Poetry creates the venv with the
              # newest Python it finds that pyproject.toml allows, and its own
              # interpreter is one of them, so a Poetry built on a newer Python
              # would put the venv on that Python instead.
              (pkgs.poetry.override { python3 = pkgs.python314; })
              pkgs.pyright
              pkgs.nodejs_24

              # cdktn, for the Terraform stacks. Keep `cdktn` in
              # iac/pyproject.toml in sync with cdktn-cli's minor version.
              pkgs.terraform
              pkgs.cdktn-cli

              # cdk8s, for the Kubernetes charts. It renders Helm charts
              # (lab/charts/grafana.py) with helm.
              cdk8s-cli
              pkgs.kubernetes-helm
            ];
          };
        }
      );
    };
}
