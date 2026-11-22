{
  description = "Homelab infrastructure-as-code";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    # nixos-25.11 is the last release with cdktf-cli, at 0.21.0. Later releases
    # replace HashiCorp's version with cdktn-cli, the CDK Terrain fork.
    #
    # Keep `cdktf` in iac/pyproject.toml in sync with cdktf-cli's minor version.
    nixpkgs-cdktf.url = "github:NixOS/nixpkgs/nixos-25.11";

    # nixpkgs only ships the latest Terraform. This project requires
    # terraform<1.15. Newer versions fail `cdktf get` on the OKE module
    # ("Missing required provider configuration ... oci.home").
    nixpkgs-terraform.url = "github:stackbuilders/nixpkgs-terraform";
  };

  outputs =
    {
      nixpkgs,
      nixpkgs-cdktf,
      nixpkgs-terraform,
      ...
    }:
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
          pkgs = nixpkgs.legacyPackages.${system};

          # `cdktf get` and `cdk8s import` use jsii-srcmak, which copies jsii
          # dependencies out of the CLI's own package into a temp dir with
          # `fs.copy`. From the read-only store, the copies keep read-only
          # modes, so deleting the temp dir fails with EACCES.
          #
          # Make each copy writable right after it is made. `--replace-fail`
          # stops the build if a version bump changes the patched code.
          chmodWritable =
            target:
            ''require("child_process").execFileSync("${pkgs.coreutils}/bin/chmod", ["-R", "u+w", ${target}])'';

          cdktf-cli = nixpkgs-cdktf.legacyPackages.${system}.cdktf-cli.overrideAttrs (old: {
            # The terraform-cdk repo keeps its packages at version 0.0.0 and
            # sets the real version when releasing with `align-version`. Without
            # this, version reports 0.0.0, and `cdktf get` skips the check that
            # the CLI and the project's cdktf library share a minor version.
            #
            # Backport NixOS/nixpkgs#465006, which adds this call, but isn't in
            # release-25.11.
            preBuild = (old.preBuild or "") + ''
              bash ./tools/align-version.sh
            '';

            postInstall = (old.postInstall or "") + ''
              # This is `await fs.copy(dir, targetdir)` in the minified bundle.
              substituteInPlace $out/lib/node_modules/cdktf-cli/bundle/bin/cmds/handlers.js \
                --replace-fail 'await Ii.copy(B,ee)' 'await Ii.copy(B,ee),${chmodWritable "ee"}'

              # The recipe copies node_modules with `cp -rL`, which follows the
              # yarn workspace symlink to cdktf's source directory. The bundled
              # cdktf library then has its .ts sources beside the .d.ts files.
              # `cdktf get` compiles bindings against it with jsii, and
              # TypeScript prefers .ts over .d.ts, so it type-checks cdktf's
              # sources, which fails without @types/node.
              #
              # Delete the .ts sources and keep the declarations, as in the
              # published npm package.
              find $out/lib/node_modules/cdktf-cli/node_modules/cdktf \
                -path '*/cdktf/node_modules' -prune -o \
                -type f -name '*.ts' ! -name '*.d.ts' -exec rm {} +
            '';
          });

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
              # Python project. The cdktf and cdk8s libraries run on Node
              # through jsii.
              pkgs.python313
              # Build Poetry on the same Python. Poetry creates the venv with the
              # newest Python it finds that pyproject.toml allows, and its own
              # interpreter is one of them, so a Poetry built on a newer Python
              # would put the venv on that Python instead.
              (pkgs.poetry.override { python3 = pkgs.python313; })
              pkgs.pyright
              pkgs.nodejs_24

              # cdktf, for the Terraform stacks
              nixpkgs-terraform.packages.${system}."terraform-1.14.9"
              cdktf-cli

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
