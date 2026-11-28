import csv

import pytest

from scripts.evaluate_intent import load_intent_splits


def write_split(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("text", "intent"))
        writer.writerows(rows)


def test_model_evaluation_rejects_train_test_overlap_after_normalization(tmp_path):
    train, test = tmp_path / "train.csv", tmp_path / "test.csv"
    write_split(train, [("Berapa harga?", "tanya_harga"), ("Halo", "sapaan")])
    write_split(
        test, [("  BERAPA   HARGA? ", "tanya_harga"), ("Selamat siang", "sapaan")]
    )
    with pytest.raises(ValueError, match="overlap"):
        load_intent_splits(train, test)


def test_model_evaluation_requires_the_same_intent_coverage(tmp_path):
    train, test = tmp_path / "train.csv", tmp_path / "test.csv"
    write_split(train, [("Berapa harga?", "tanya_harga"), ("Halo", "sapaan")])
    write_split(test, [("Selamat siang", "sapaan"), ("Ada stok?", "tanya_stok")])
    with pytest.raises(ValueError, match="same labels"):
        load_intent_splits(train, test)


def test_model_evaluation_loads_distinct_valid_splits(tmp_path):
    train, test = tmp_path / "train.csv", tmp_path / "test.csv"
    train_rows = [("Berapa harga?", "tanya_harga"), ("Halo", "sapaan")]
    test_rows = [("Selamat siang", "sapaan"), ("Harganya berapa?", "tanya_harga")]
    write_split(train, train_rows)
    write_split(test, test_rows)
    assert load_intent_splits(train, test) == (train_rows, test_rows)


def test_model_evaluation_rejects_overlap_from_slang_and_unit_normalization(tmp_path):
    train, test = tmp_path / "train.csv", tmp_path / "test.csv"
    write_split(train, [("Mau psn 1kg min", "pemesanan"), ("Halo", "sapaan")])
    write_split(
        test, [("Mau pesan 1 kg kak", "pemesanan"), ("Selamat siang", "sapaan")]
    )
    with pytest.raises(ValueError, match="overlap"):
        load_intent_splits(train, test)


def test_model_evaluation_accepts_the_provisional_dataset_label(tmp_path):
    train, test = tmp_path / "train.csv", tmp_path / "test.csv"
    train_rows = [("Berapa harga?", "tanya_produk"), ("Halo", "lainnya")]
    test_rows = [("Selamat siang", "lainnya"), ("Harganya berapa?", "tanya_produk")]
    write_split(train, train_rows)
    write_split(test, test_rows)
    assert load_intent_splits(train, test) == (train_rows, test_rows)
