import unittest

from nqmate_api.ml.boosted import LightGBMClassifier, SklearnGradientBoostingClassifier, XGBoostClassifier, XGBoostConfig


class XGBoostTests(unittest.TestCase):
    def test_unfitted_model_rejects_prediction(self) -> None:
        with self.assertRaises(RuntimeError):
            XGBoostClassifier().predict_probability(((1.0,),))

    def test_xgboost_adapter_learns_simple_training_shape(self) -> None:
        try:
            model = XGBoostClassifier(XGBoostConfig(n_estimators=8)).fit(((0.0,), (1.0,), (2.0,), (3.0,)), (0, 0, 1, 1))
        except RuntimeError as error:
            self.skipTest(str(error))
        probabilities = model.predict_probability(((0.0,), (3.0,)))
        self.assertEqual(len(probabilities), 2)
        self.assertTrue(all(0 <= probability <= 1 for probability in probabilities))

    def test_other_boosting_adapters_return_probabilities(self) -> None:
        for classifier in (SklearnGradientBoostingClassifier(), LightGBMClassifier()):
            try:
                probabilities = classifier.fit(((0.0,), (1.0,), (2.0,), (3.0,)), (0, 0, 1, 1)).predict_probability(((0.0,), (3.0,)))
            except RuntimeError as error:
                self.skipTest(str(error))
            self.assertEqual(len(probabilities), 2)
            self.assertTrue(all(0 <= probability <= 1 for probability in probabilities))
