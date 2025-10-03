"""Tests for CLI interface."""

from unittest.mock import patch

from typer.testing import CliRunner

from src.osheightsmith.cli import app

runner = CliRunner()


class TestGenerateCommand:
    """Test the generate command."""

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_basic(self, mock_generator_class, tmp_path):
        """Test basic generate command."""
        # Setup mock
        mock_generator = mock_generator_class.return_value
        output_path = str(tmp_path / "output.png")
        mock_generator.generate_heightmap.return_value = (output_path, 200, 200)

        # Create a temporary zip file
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(app, ["generate", "ST1876", "--zip-path", str(zip_path)])

        assert result.exit_code == 0
        assert "✓" in result.stdout or "successfully" in result.stdout.lower()
        mock_generator.generate_heightmap.assert_called_once()

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_with_options(self, mock_generator_class, tmp_path):
        """Test generate command with all options."""
        mock_generator = mock_generator_class.return_value
        output_path = str(tmp_path / "custom_output.png")
        mock_generator.generate_heightmap.return_value = (output_path, 400, 400)

        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(
            app,
            [
                "generate",
                "ST1876",
                "--size",
                "20",
                "--zip-path",
                str(zip_path),
                "--output",
                output_path,
                "--bit-depth",
                "16",
            ],
        )

        assert result.exit_code == 0
        mock_generator.generate_heightmap.assert_called_once_with(
            grid_ref="ST1876", size_km=20, output_path=output_path, bit_depth=16, fill_missing=True
        )

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_with_short_options(self, mock_generator_class, tmp_path):
        """Test generate command with short option flags."""
        mock_generator = mock_generator_class.return_value
        output_path = str(tmp_path / "output.png")
        mock_generator.generate_heightmap.return_value = (output_path, 200, 200)

        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(
            app,
            ["generate", "ST1876", "-s", "15", "-z", str(zip_path), "-o", output_path, "-b", "8"],
        )

        assert result.exit_code == 0
        mock_generator.generate_heightmap.assert_called_once_with(
            grid_ref="ST1876", size_km=15, output_path=output_path, bit_depth=8, fill_missing=True
        )

    def test_generate_invalid_bit_depth(self, tmp_path):
        """Test generate command with invalid bit depth."""
        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(
            app, ["generate", "ST1876", "--bit-depth", "32", "--zip-path", str(zip_path)]
        )

        assert result.exit_code == 1
        assert "bit-depth must be 8 or 16" in result.stdout.lower()

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_missing_zip_file(self, mock_generator_class):
        """Test generate command with missing zip file."""
        mock_generator_class.side_effect = FileNotFoundError(
            "Terrain data not found: data/missing.zip"
        )

        result = runner.invoke(app, ["generate", "ST1876", "--zip-path", "data/missing.zip"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_invalid_grid_reference(self, mock_generator_class, tmp_path):
        """Test generate command with invalid grid reference."""
        mock_generator = mock_generator_class.return_value
        mock_generator.generate_heightmap.side_effect = ValueError(
            "Invalid grid reference format: ZZ9999"
        )

        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(app, ["generate", "ZZ9999", "--zip-path", str(zip_path)])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_no_tiles_found(self, mock_generator_class, tmp_path):
        """Test generate command when no tiles are found."""
        mock_generator = mock_generator_class.return_value
        mock_generator.generate_heightmap.side_effect = FileNotFoundError(
            "No terrain data found for area ST1876"
        )

        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(app, ["generate", "ST1876", "--zip-path", str(zip_path)])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    def test_generate_missing_grid_ref_argument(self):
        """Test generate command without required grid reference argument."""
        result = runner.invoke(app, ["generate"])

        assert result.exit_code != 0
        # Typer will show usage/error message

    @patch("src.osheightsmith.cli.HeightmapGenerator")
    def test_generate_with_no_fill_missing(self, mock_generator_class, tmp_path):
        """Test generate command with --no-fill-missing flag."""
        mock_generator = mock_generator_class.return_value
        output_path = str(tmp_path / "output.png")
        mock_generator.generate_heightmap.return_value = (output_path, 200, 200)

        zip_path = tmp_path / "test.zip"
        zip_path.touch()

        result = runner.invoke(
            app, ["generate", "ST1876", "--zip-path", str(zip_path), "--no-fill-missing"]
        )

        assert result.exit_code == 0
        mock_generator.generate_heightmap.assert_called_once()
        # Verify fill_missing=False was passed
        call_kwargs = mock_generator.generate_heightmap.call_args.kwargs
        assert call_kwargs["fill_missing"] is False


class TestInfoCommand:
    """Test the info command."""

    def test_info_basic(self):
        """Test basic info command."""
        result = runner.invoke(app, ["info", "ST1876"])

        assert result.exit_code == 0
        assert "ST1876" in result.stdout.upper()
        assert "318,000" in result.stdout or "318000" in result.stdout
        assert "176,000" in result.stdout or "176000" in result.stdout

    def test_info_with_size_option(self):
        """Test info command with custom size."""
        result = runner.invoke(app, ["info", "ST1876", "--size", "20"])

        assert result.exit_code == 0
        assert "20 km" in result.stdout

    def test_info_with_short_option(self):
        """Test info command with short option flag."""
        result = runner.invoke(app, ["info", "ST1876", "-s", "15"])

        assert result.exit_code == 0
        assert "15 km" in result.stdout

    def test_info_different_grid_references(self):
        """Test info command with various grid references."""
        test_refs = ["TQ3080", "NN1234", "SV0000"]

        for grid_ref in test_refs:
            result = runner.invoke(app, ["info", grid_ref])
            assert result.exit_code == 0
            assert grid_ref.upper() in result.stdout

    def test_info_invalid_grid_reference(self):
        """Test info command with invalid grid reference."""
        result = runner.invoke(app, ["info", "ZZ9999"])

        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    def test_info_shows_tile_information(self):
        """Test that info command displays tile information."""
        result = runner.invoke(app, ["info", "ST1876"])

        assert result.exit_code == 0
        assert "tiles" in result.stdout.lower() or "tile" in result.stdout.lower()

    def test_info_shows_coordinates(self):
        """Test that info command displays coordinate information."""
        result = runner.invoke(app, ["info", "ST1876"])

        assert result.exit_code == 0
        assert "easting" in result.stdout.lower()
        assert "northing" in result.stdout.lower()

    def test_info_shows_precision(self):
        """Test that info command displays precision information."""
        result = runner.invoke(app, ["info", "ST1876"])

        assert result.exit_code == 0
        assert "precision" in result.stdout.lower()

    def test_info_missing_grid_ref_argument(self):
        """Test info command without required grid reference argument."""
        result = runner.invoke(app, ["info"])

        assert result.exit_code != 0
        # Typer will show usage/error message


class TestCLIHelp:
    """Test CLI help functionality."""

    def test_app_help(self):
        """Test main app help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "osheightsmith" in result.stdout.lower() or "heightmap" in result.stdout.lower()

    def test_generate_help(self):
        """Test generate command help."""
        result = runner.invoke(app, ["generate", "--help"])

        assert result.exit_code == 0
        assert "generate" in result.stdout.lower()
        assert "grid" in result.stdout.lower()

    def test_info_help(self):
        """Test info command help."""
        result = runner.invoke(app, ["info", "--help"])

        assert result.exit_code == 0
        assert "info" in result.stdout.lower()
