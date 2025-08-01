# SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from unittest.mock import MagicMock, patch

import pytest
import torch
from transformers.modeling_outputs import SequenceClassifierOutput

from haystack import Document
from haystack.components.rankers.transformers_similarity import TransformersSimilarityRanker
from haystack.utils.auth import Secret
from haystack.utils.device import ComponentDevice, DeviceMap


class TestSimilarityRanker:
    def test_to_dict(self):
        component = TransformersSimilarityRanker()
        data = component.to_dict()
        assert data == {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {
                "device": None,
                "top_k": 10,
                "token": {"env_vars": ["HF_API_TOKEN", "HF_TOKEN"], "strict": False, "type": "env_var"},
                "query_prefix": "",
                "document_prefix": "",
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "meta_fields_to_embed": [],
                "embedding_separator": "\n",
                "scale_score": True,
                "calibration_factor": 1.0,
                "score_threshold": None,
                "model_kwargs": {"device_map": ComponentDevice.resolve_device(None).to_hf()},
                "tokenizer_kwargs": {},
                "batch_size": 16,
            },
        }

    def test_to_dict_with_custom_init_parameters(self):
        component = TransformersSimilarityRanker(
            model="my_model",
            device=ComponentDevice.from_str("cuda:0"),
            token=Secret.from_env_var("ENV_VAR", strict=False),
            top_k=5,
            query_prefix="query_instruction: ",
            document_prefix="document_instruction: ",
            scale_score=False,
            calibration_factor=None,
            score_threshold=0.01,
            model_kwargs={"torch_dtype": torch.float16},
            tokenizer_kwargs={"model_max_length": 512},
            batch_size=32,
        )
        data = component.to_dict()
        assert data == {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {
                "device": None,
                "model": "my_model",
                "token": {"env_vars": ["ENV_VAR"], "strict": False, "type": "env_var"},
                "top_k": 5,
                "query_prefix": "query_instruction: ",
                "document_prefix": "document_instruction: ",
                "meta_fields_to_embed": [],
                "embedding_separator": "\n",
                "scale_score": False,
                "calibration_factor": None,
                "score_threshold": 0.01,
                "model_kwargs": {
                    "torch_dtype": "torch.float16",
                    "device_map": ComponentDevice.from_str("cuda:0").to_hf(),
                },  # torch_dtype is correctly serialized
                "tokenizer_kwargs": {"model_max_length": 512},
                "batch_size": 32,
            },
        }

    def test_to_dict_with_quantization_options(self):
        component = TransformersSimilarityRanker(
            model_kwargs={
                "load_in_4bit": True,
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_compute_dtype": torch.bfloat16,
            }
        )
        data = component.to_dict()
        assert data == {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {
                "device": None,
                "top_k": 10,
                "query_prefix": "",
                "document_prefix": "",
                "token": {"env_vars": ["HF_API_TOKEN", "HF_TOKEN"], "strict": False, "type": "env_var"},
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "meta_fields_to_embed": [],
                "embedding_separator": "\n",
                "scale_score": True,
                "calibration_factor": 1.0,
                "score_threshold": None,
                "model_kwargs": {
                    "load_in_4bit": True,
                    "bnb_4bit_use_double_quant": True,
                    "bnb_4bit_quant_type": "nf4",
                    "bnb_4bit_compute_dtype": "torch.bfloat16",
                    "device_map": ComponentDevice.resolve_device(None).to_hf(),
                },
                "tokenizer_kwargs": {},
                "batch_size": 16,
            },
        }

    @pytest.mark.parametrize(
        "device_map,expected",
        [
            ("auto", "auto"),
            ("cpu:0", ComponentDevice.from_str("cpu:0").to_hf()),
            ({"": "cpu:0"}, ComponentDevice.from_multiple(DeviceMap.from_hf({"": "cpu:0"})).to_hf()),
        ],
    )
    def test_to_dict_device_map(self, device_map, expected):
        component = TransformersSimilarityRanker(model_kwargs={"device_map": device_map}, token=None)
        data = component.to_dict()

        assert data == {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {
                "device": None,
                "top_k": 10,
                "token": None,
                "query_prefix": "",
                "document_prefix": "",
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "meta_fields_to_embed": [],
                "embedding_separator": "\n",
                "scale_score": True,
                "calibration_factor": 1.0,
                "score_threshold": None,
                "model_kwargs": {"device_map": expected},
                "tokenizer_kwargs": {},
                "batch_size": 16,
            },
        }

    def test_from_dict(self):
        data = {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {
                "device": None,
                "model": "my_model",
                "token": None,
                "top_k": 5,
                "query_prefix": "",
                "document_prefix": "",
                "meta_fields_to_embed": [],
                "embedding_separator": "\n",
                "scale_score": False,
                "calibration_factor": None,
                "score_threshold": 0.01,
                "model_kwargs": {"torch_dtype": "torch.float16"},
                "tokenizer_kwargs": {"model_max_length": 512},
                "batch_size": 32,
            },
        }

        component = TransformersSimilarityRanker.from_dict(data)
        assert component.device is None
        assert component.model_name_or_path == "my_model"
        assert component.token is None
        assert component.top_k == 5
        assert component.query_prefix == ""
        assert component.document_prefix == ""
        assert component.meta_fields_to_embed == []
        assert component.embedding_separator == "\n"
        assert not component.scale_score
        assert component.calibration_factor is None
        assert component.score_threshold == 0.01
        # torch_dtype is correctly deserialized
        assert component.model_kwargs == {
            "torch_dtype": torch.float16,
            "device_map": ComponentDevice.resolve_device(None).to_hf(),
        }
        assert component.tokenizer_kwargs == {"model_max_length": 512}
        assert component.batch_size == 32

    def test_from_dict_no_default_parameters(self):
        data = {
            "type": "haystack.components.rankers.transformers_similarity.TransformersSimilarityRanker",
            "init_parameters": {},
        }

        component = TransformersSimilarityRanker.from_dict(data)
        assert component.device is None
        assert component.model_name_or_path == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert component.token == Secret.from_env_var(["HF_API_TOKEN", "HF_TOKEN"], strict=False)
        assert component.top_k == 10
        assert component.query_prefix == ""
        assert component.document_prefix == ""
        assert component.meta_fields_to_embed == []
        assert component.embedding_separator == "\n"
        assert component.scale_score
        assert component.calibration_factor == 1.0
        assert component.score_threshold is None
        # torch_dtype is correctly deserialized
        assert component.model_kwargs == {"device_map": ComponentDevice.resolve_device(None).to_hf()}
        assert component.tokenizer_kwargs == {}
        assert component.batch_size == 16

    @patch("torch.sigmoid")
    @patch("torch.sort")
    @patch("torch.stack")
    def test_embed_meta(self, mocked_stack, mocked_sort, mocked_sigmoid):
        mocked_stack.return_value = torch.tensor([0])
        mocked_sort.return_value = (None, torch.tensor([0]))
        mocked_sigmoid.return_value = torch.tensor([0])
        embedder = TransformersSimilarityRanker(
            model="model", meta_fields_to_embed=["meta_field"], embedding_separator="\n"
        )
        embedder.model = MagicMock()
        embedder.tokenizer = MagicMock()
        embedder.device = MagicMock()
        embedder.warm_up()

        documents = [Document(content=f"document number {i}", meta={"meta_field": f"meta_value {i}"}) for i in range(5)]

        embedder.run(query="test", documents=documents)

        embedder.tokenizer.assert_called_once_with(
            [
                ["test", "meta_value 0\ndocument number 0"],
                ["test", "meta_value 1\ndocument number 1"],
                ["test", "meta_value 2\ndocument number 2"],
                ["test", "meta_value 3\ndocument number 3"],
                ["test", "meta_value 4\ndocument number 4"],
            ],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

    @patch("torch.sigmoid")
    @patch("torch.sort")
    @patch("torch.stack")
    def test_prefix(self, mocked_stack, mocked_sort, mocked_sigmoid):
        mocked_stack.return_value = torch.tensor([0])
        mocked_sort.return_value = (None, torch.tensor([0]))
        mocked_sigmoid.return_value = torch.tensor([0])
        embedder = TransformersSimilarityRanker(
            model="model", query_prefix="query_instruction: ", document_prefix="document_instruction: "
        )
        embedder.model = MagicMock()
        embedder.tokenizer = MagicMock()
        embedder.device = MagicMock()
        embedder.warm_up()

        documents = [Document(content=f"document number {i}", meta={"meta_field": f"meta_value {i}"}) for i in range(5)]

        embedder.run(query="test", documents=documents)

        embedder.tokenizer.assert_called_once_with(
            [
                ["query_instruction: test", "document_instruction: document number 0"],
                ["query_instruction: test", "document_instruction: document number 1"],
                ["query_instruction: test", "document_instruction: document number 2"],
                ["query_instruction: test", "document_instruction: document number 3"],
                ["query_instruction: test", "document_instruction: document number 4"],
            ],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

    @patch("torch.sort")
    @patch("torch.stack")
    def test_scale_score_false(self, mocked_stack, mocked_sort):
        mocked_stack.return_value = torch.FloatTensor([-10.6859, -8.9874])
        mocked_sort.return_value = (None, torch.tensor([0, 1]))
        embedder = TransformersSimilarityRanker(model="model", scale_score=False)
        embedder.model = MagicMock()
        embedder.model.return_value = SequenceClassifierOutput(
            loss=None, logits=torch.FloatTensor([[-10.6859], [-8.9874]]), hidden_states=None, attentions=None
        )
        embedder.tokenizer = MagicMock()
        embedder.device = MagicMock()

        documents = [Document(content="document number 0"), Document(content="document number 1")]
        out = embedder.run(query="test", documents=documents)
        assert out["documents"][0].score == pytest.approx(-10.6859, abs=1e-4)
        assert out["documents"][1].score == pytest.approx(-8.9874, abs=1e-4)

    @patch("torch.sort")
    @patch("torch.stack")
    def test_score_threshold(self, mocked_stack, mocked_sort):
        mocked_stack.return_value = torch.FloatTensor([0.955, 0.001])
        mocked_sort.return_value = (None, torch.tensor([0, 1]))
        embedder = TransformersSimilarityRanker(model="model", scale_score=False, score_threshold=0.1)
        embedder.model = MagicMock()
        embedder.model.return_value = SequenceClassifierOutput(
            loss=None, logits=torch.FloatTensor([[0.955], [0.001]]), hidden_states=None, attentions=None
        )
        embedder.tokenizer = MagicMock()
        embedder.device = MagicMock()

        documents = [Document(content="document number 0"), Document(content="document number 1")]
        out = embedder.run(query="test", documents=documents)
        assert len(out["documents"]) == 1

    def test_device_map_and_device_raises(self, caplog):
        with caplog.at_level(logging.WARNING):
            _ = TransformersSimilarityRanker(
                "model", model_kwargs={"device_map": "cpu"}, device=ComponentDevice.from_str("cuda")
            )
            assert (
                "The parameters `device` and `device_map` from `model_kwargs` are both provided. Ignoring `device` "
                "and using `device_map`." in caplog.text
            )

    @patch("haystack.components.rankers.transformers_similarity.AutoTokenizer.from_pretrained")
    @patch("haystack.components.rankers.transformers_similarity.AutoModelForSequenceClassification.from_pretrained")
    def test_device_map_dict(self, mocked_automodel, _mocked_autotokenizer, monkeypatch):
        monkeypatch.delenv("HF_API_TOKEN", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)
        ranker = TransformersSimilarityRanker("model", model_kwargs={"device_map": {"layer_1": 1, "classifier": "cpu"}})

        class MockedModel:
            def __init__(self):
                self.hf_device_map = {"layer_1": 1, "classifier": "cpu"}

        mocked_automodel.return_value = MockedModel()
        ranker.warm_up()

        mocked_automodel.assert_called_once_with("model", token=None, device_map={"layer_1": 1, "classifier": "cpu"})
        assert ranker.device == ComponentDevice.from_multiple(DeviceMap.from_hf({"layer_1": 1, "classifier": "cpu"}))

    @pytest.mark.integration
    @pytest.mark.slow
    def test_run(self):
        """
        Test if the component ranks documents correctly.
        """
        ranker = TransformersSimilarityRanker(model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        ranker.warm_up()

        query = "City in Bosnia and Herzegovina"
        docs_before_texts = ["Berlin", "Belgrade", "Sarajevo"]
        expected_first_text = "Sarajevo"
        expected_scores = [2.2864143829792738e-05, 0.00012495707778725773, 0.009869757108390331]

        docs_before = [Document(content=text) for text in docs_before_texts]
        output = ranker.run(query=query, documents=docs_before)
        docs_after = output["documents"]

        assert len(docs_after) == 3
        assert docs_after[0].content == expected_first_text

        sorted_scores = sorted(expected_scores, reverse=True)
        assert docs_after[0].score == pytest.approx(sorted_scores[0], abs=1e-6)
        assert docs_after[1].score == pytest.approx(sorted_scores[1], abs=1e-6)
        assert docs_after[2].score == pytest.approx(sorted_scores[2], abs=1e-6)

    def test_returns_empty_list_if_no_documents_are_provided(self):
        sampler = TransformersSimilarityRanker()
        sampler.model = MagicMock()

        output = sampler.run(query="City in Germany", documents=[])
        assert not output["documents"]

    #  Raises ComponentError if model is not warmed up
    def test_raises_component_error_if_model_not_warmed_up(self):
        sampler = TransformersSimilarityRanker()
        with pytest.raises(RuntimeError):
            sampler.run(query="query", documents=[Document(content="document")])

    @pytest.mark.integration
    @pytest.mark.slow
    def test_run_top_k(self):
        """
        Test if the component ranks documents correctly with a custom top_k.
        """
        ranker = TransformersSimilarityRanker(model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_k=2)
        ranker.warm_up()

        query = "City in Bosnia and Herzegovina"
        docs_before_texts = ["Berlin", "Belgrade", "Sarajevo"]
        expected_first_text = "Sarajevo"

        docs_before = [Document(content=text) for text in docs_before_texts]
        output = ranker.run(query=query, documents=docs_before)
        docs_after = output["documents"]

        assert len(docs_after) == 2
        assert docs_after[0].content == expected_first_text

        sorted_scores = sorted([doc.score for doc in docs_after], reverse=True)
        assert [doc.score for doc in docs_after] == sorted_scores

    @pytest.mark.integration
    @pytest.mark.slow
    def test_run_single_document(self):
        """
        Test if the component runs with a single document.
        """
        ranker = TransformersSimilarityRanker(model="cross-encoder/ms-marco-MiniLM-L-6-v2", device=None)
        ranker.warm_up()
        docs_before = [Document(content="Berlin")]
        output = ranker.run(query="City in Germany", documents=docs_before)
        docs_after = output["documents"]

        assert len(docs_after) == 1
