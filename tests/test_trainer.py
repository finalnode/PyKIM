import pytest
import pykim

from pykim import down, left, paint, paint_path, right, set_x, set_y, up
from pykim.trainer.runner import check_exercise
from pykim.trainer.optimization import evaluate_stairs


def efficient_stairs():
    paint_path("purple")
    for _ in range(5):
        right(5)
        down(5)


def repeated_stairs():
    paint_path("purple")
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)
    right(5)
    down(5)


def draw_multiple_pixels_example():
    pykim.kim.set_position(20, 20)
    pykim.kim.paint_path("purple")
    mia = pykim.world.new_pixel("MIA", x=60, y=20)
    mia.paint_path("orange")
    leo = pykim.world.new_pixel("LEO", x=40, y=60)
    leo.paint_path("cyan")

    with pykim.world.parallel():
        pykim.kim.right(15)
        mia.left(15)
        leo.up(20)

    pykim.kim.down(10)
    mia.down(20)
    leo.right(10)

    with pykim.world.parallel():
        pykim.kim.right(15)
        mia.left(15)
        leo.up(15)
    leo.hide()


def test_square_exercise_accepts_a_complete_square(capsys):
    set_x(50)
    set_y(50)
    paint_path("purple")
    right(5)
    down(5)
    left(5)
    up(5)

    report = check_exercise("quadrat-5", "")

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "5 Pixel breit" in output
    assert "vollständig gelöst" in output


def test_square_exercise_accepts_another_direction(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    down(5)
    right(5)
    up(5)
    left(5)

    assert check_exercise("quadrat-5", "").successful
    capsys.readouterr()


def test_square_exercise_gives_several_hints_for_an_incomplete_solution(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    right(5)
    down(4)

    report = check_exercise("quadrat-5", "")

    assert not report.successful
    assert report.passed < 5
    output = capsys.readouterr().out
    assert "✗ Start oder Ende des Quadrats liegt nicht bei (50, 50)" in output
    assert "Hinweis:" in output
    assert "Prüfungen bestanden" in output


def test_square_exercise_rejects_an_extra_pixel(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    right(5)
    down(5)
    left(5)
    up(5)
    right(1)
    down(1)
    paint()

    report = check_exercise("quadrat-5", "")

    assert not report.successful
    assert not report.results[-1].passed
    capsys.readouterr()


def test_stairs_accept_complete_drawing_with_a_loop(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()

    report = check_exercise("treppe-5", "for _ in range(5): pass")

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "5 Stufen" in output
    assert "vermeidest Wiederholungen" in output


def test_stairs_reports_optimal_code_score(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()
    source = """
for _ in range(5):
    right(5)
    down(5)
"""

    report = check_exercise("treppe-5", source)

    assert report.optimization is not None
    assert report.optimization.score == 10
    output = capsys.readouterr().out
    assert "Optimierung: 10/10" in output
    assert "optimal aufgebaut" in output


def test_stairs_gives_optimization_tips_for_repeated_code(capsys):
    source = "\n".join(["right(5)", "down(5)"] * 5)

    optimization = evaluate_stairs(source)

    assert optimization.score == 1
    assert any("Schleife" in tip for tip in optimization.tips)
    assert any("jeweils nur einmal" in tip for tip in optimization.tips)


def test_stairs_encourage_shorter_code(capsys):
    set_x(50)
    set_y(50)
    repeated_stairs()

    report = check_exercise("treppe-5", "right(5)\ndown(5)")

    assert not report.successful
    assert all(result.passed for result in report.results[:-1])
    assert not report.results[-1].passed
    assert "Code lässt sich noch kürzen" in capsys.readouterr().out


def test_stairs_reject_a_missing_step(capsys):
    set_x(50)
    set_y(50)
    paint_path()
    for _ in range(4):
        right(5)
        down(5)

    report = check_exercise("treppe-5", "for _ in range(4): pass")

    assert not report.successful
    assert not report.results[0].passed
    assert not report.results[1].passed
    assert "unvollständig" in capsys.readouterr().out


def test_run_style_check_detects_a_loop_without_a_function(capsys):
    set_x(50)
    set_y(50)
    efficient_stairs()
    source = """
paint_path()
for _ in range(5):
    right(5)
    down(5)
"""

    report = check_exercise("treppe-5", source)

    assert report.successful
    assert "vermeidest Wiederholungen" in capsys.readouterr().out


def test_run_style_check_rejects_an_unknown_exercise():
    with pytest.raises(ValueError, match="gibt es nicht"):
        check_exercise("unbekannt", "for _ in range(5): pass")


def test_multiple_pixels_exercise_checks_world_drawing_and_parallel(capsys):
    draw_multiple_pixels_example()

    report = check_exercise(
        "mehrere-pixel", "with world.parallel():\n    kim.right(15)"
    )

    assert report.successful
    assert report.passed == 5
    output = capsys.readouterr().out
    assert "farbigen Linien stimmen exakt" in output
    assert "world.parallel()-Block" in output


def test_multiple_pixels_exercise_detects_a_wrong_world_pixel(capsys):
    draw_multiple_pixels_example()
    pykim.world.cells[20][20] = 9

    report = check_exercise(
        "mehrere-pixel", "with world.parallel():\n    kim.right(15)"
    )

    assert not report.results[2].passed
    assert "Farben weichen" in capsys.readouterr().out


def test_multiple_pixels_exercise_requires_parallel_source(capsys):
    draw_multiple_pixels_example()

    report = check_exercise("mehrere-pixel", "kim.right(15)")

    assert all(result.passed for result in report.results[:-1])
    assert not report.results[-1].passed
    assert "noch nicht parallel" in capsys.readouterr().out
