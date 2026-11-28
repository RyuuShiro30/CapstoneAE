import unittest

from app.preprocessing import clean_text, preprocess_batch


class TestPreprocessing(unittest.TestCase):
    def test_slang_and_units(self):
        raw = "Bang, hrg gurame 2kg brp? Readyyy gak buat bkr2??"
        expected = "admin harga gurame 2 kg berapa tersedia tidak buat bakar 2"
        self.assertEqual(clean_text(raw), expected)

    def test_empty_and_whitespace(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("     "), "")
        self.assertEqual(clean_text(None), "")

    def test_symbols_only(self):
        self.assertEqual(clean_text("!@#$%^&*()_+-=[]{};':\",./<>?"), "")

    def test_numbers_only(self):
        self.assertEqual(clean_text("12345 67890"), "12345 67890")

    def test_quantity_preserves_repeated_digits(self):
        self.assertEqual(clean_text("Mau psn 1000kg"), "mau pesan 1000 kg")

    def test_url_and_mention_removal(self):
        raw = "Cek katalog https://contoh.com @mangujang #gurame mantap!"
        self.assertEqual(clean_text(raw), "cek katalog mantap")

    def test_batch_processing(self):
        inputs = ["Brp hrga?", "   ", "Mau psn 1kg"]
        outputs = preprocess_batch(inputs)
        self.assertEqual(outputs, ["berapa harga", "", "mau pesan 1 kg"])


if __name__ == "__main__":
    unittest.main()
