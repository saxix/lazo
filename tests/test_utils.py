import pytest

from lazo.utils import jprint


# from lazo.utils import import_by_name

#
# @pytest.mark.parametrize("value, expected", [(1024**8, "1.0YiB"),
#                                              (1, "1.0B"), (10, "10.0B"), (128, "128.0B"),
#                                              (1024, "1.0KiB"),
#                                              (10000, "9.8KiB"),
#                                              (1048576, "1.0MiB")])
# def test_sizeof(value, expected):
#     assert sizeof(value) == expected

#
# def test_import_by_name():
#
#     with pytest.raises(ValueError):
#         import_by_name("")
#
#     with pytest.raises(TypeError):
#         import_by_name(1)
#
#     with pytest.raises(ValueError):
#         import_by_name('object')
#
#     with pytest.raises(AttributeError):
#         import_by_name('lazo.error')


def test_jprint_no_colors(capsys):
    jprint({}, False)
    captured = capsys.readouterr()
    assert captured.out == "{}\n"


def test_jprint_colors(capsys):
    jprint({}, True)
    captured = capsys.readouterr()
    assert captured.out == "{}\x1b[37m\x1b[39;49;00m\n\n"
