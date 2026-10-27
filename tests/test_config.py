"""config.py 的基本檢查：參數存在且數值合理。"""

import numpy as np
import pytest

from board.config import (
    CAMERA_HFOV_DEG,
    CAMERA_MOUNT,
    CAMERA_RANGE_M,
    CHECK_ALTITUDE,
    DROP_ALTITUDE,
    DROP_AREA,
    DROP_DRIFT,
    HOVER_POS_ERROR,
    PAYLOAD_SIZE,
    SCORE_WEIGHTS,
)


def test_altitudes() -> None:
    assert 0 < DROP_ALTITUDE < CHECK_ALTITUDE


def test_drop_area() -> None:
    assert len(DROP_AREA) == 2
    assert all(side > 0 for side in DROP_AREA)


def test_drop_area_formula() -> None:
    """投放面積 = 物資大小 + 2 ×（位置誤差 + 落下偏移）。"""
    margin = 2 * (HOVER_POS_ERROR + DROP_DRIFT)
    assert DROP_AREA[0] == pytest.approx(PAYLOAD_SIZE[0] + margin)
    assert DROP_AREA[1] == pytest.approx(PAYLOAD_SIZE[1] + margin)


def test_drop_area_fits_in_view_at_drop_altitude() -> None:
    """在投放高度時，相機正下方拍到的地面寬度要能涵蓋整個投放區域。"""
    view_width = 2 * DROP_ALTITUDE * np.tan(np.radians(CAMERA_HFOV_DEG / 2))
    assert max(DROP_AREA) < view_width


def test_score_weights_sum_to_one() -> None:
    assert set(SCORE_WEIGHTS) == {"slope", "roughness", "protrusion"}
    assert sum(SCORE_WEIGHTS.values()) == pytest.approx(1.0)


def test_camera_range_covers_check_altitude() -> None:
    near, far = CAMERA_RANGE_M
    assert 0 < near < DROP_ALTITUDE
    assert far > CHECK_ALTITUDE
    assert 0 < CAMERA_HFOV_DEG < 180


def test_camera_mount_rotation_is_valid() -> None:
    """旋轉矩陣必須正交且行列式為 1（純旋轉，不含鏡射）。"""
    r = np.array(CAMERA_MOUNT["rotation"])
    assert r.shape == (3, 3)
    np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-9)
    assert np.linalg.det(r) == pytest.approx(1.0)


def test_camera_mount_default_axes() -> None:
    """預設安裝（spec 4.4）：相機 x → 機身 y、相機 y → 機身 −x、相機 z → 機身 z。"""
    r = np.array(CAMERA_MOUNT["rotation"])
    np.testing.assert_allclose(r @ [1, 0, 0], [0, 1, 0])
    np.testing.assert_allclose(r @ [0, 1, 0], [-1, 0, 0])
    np.testing.assert_allclose(r @ [0, 0, 1], [0, 0, 1])
