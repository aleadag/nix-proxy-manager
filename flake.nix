{
  description = "A Nix-flake-based Python development environment";

  inputs.nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1.0.tar.gz";

  outputs =
    { self, nixpkgs }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forEachSupportedSystem =
        f:
        nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            pkgs = import nixpkgs { inherit system; };
          }
        );
    in
    {
      packages = forEachSupportedSystem (
        { pkgs }:
        let
          python = pkgs.python3;
        in
        rec {
          nix-proxy-manager = python.pkgs.buildPythonApplication rec {
            pname = "nix-proxy-manager";
            version = "0.1";
            format = "pyproject";

            src = ./.;

            propagatedBuildInputs = with python.pkgs; [ setuptools ];

            checkPhase = ''
              runHook preCheck
              ${python.interpreter} -m py_compile main.py
              runHook postCheck
            '';
          };
          default = nix-proxy-manager;
        }
      );

      devShells = forEachSupportedSystem (
        { pkgs }:
        let
          python = pkgs.python3;
        in
        {
          default = pkgs.mkShellNoCC {
            packages = [
              python.pkgs.pip
            ];
          };
        }
      );
    };
}
