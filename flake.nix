{
  description = "My PyQt5 + Xlib + keyboard dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (
              ps: with ps; [
                pyqt5
                xlib
                keyboard
                pillow # Add PIL for image processing as fallback
              ]
            ))
            qt5.qtbase
            qt5.qtwayland
            qt5.qtimageformats # This provides JPEG, TIFF, WEBP support!
            libjpeg # JPEG library
            imagemagick # Add ImageMagick for testing
            # Screen capture and window management tools
            grim # Wayland screen capture
            maim # X11 screen capture
            wmctrl # Window management
            xorg.xwininfo # Window geometry info
          ];

          shellHook = ''
            # Set up Qt plugin paths properly
            export QT_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins:${pkgs.qt5.qtimageformats}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
            # export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms"

            echo "🛠️  Dev-shell ready!"
            echo "🖼️  Qt plugin path: $QT_PLUGIN_PATH"
            echo "🖼️  Platform plugins: $QT_QPA_PLATFORM_PLUGIN_PATH"

            # List available image format plugins
            echo "📷 Available image format plugins:"
            echo "   From qtbase:"
            ls -la ${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/imageformats/ 2>/dev/null || echo "   qtbase imageformats not found"
            echo "   From qtimageformats:"
            ls -la ${pkgs.qt5.qtimageformats}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/imageformats/ 2>/dev/null || echo "   qtimageformats not found"
          '';
        };
      }
    );
}
