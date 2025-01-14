# Filename : model.py
from __future__ import print_function

import torch
from torch import nn

from torch.nn import CrossEntropyLoss, MSELoss
from transformers import BertForSequenceClassification, BertModel


class BertForSequenceClassificationWithDP(BertForSequenceClassification):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.bert = BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, self.config.num_labels)
        # self.classifier_proj = nn.Linear(config.projected_dim, self.config.num_labels)

        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            NU=None,
            dp_opts=None,
            noise=None,
            projection_matrix=None,
    ):
        r"""
        labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size,)`, `optional`, defaults to :obj:`None`):
            Labels for computing the sequence classification/regression loss.
            Indices should be in :obj:`[0, ..., config.num_labels - 1]`.
            If :obj:`config.num_labels == 1` a regression loss is computed (Mean-Square loss),
            If :obj:`config.num_labels > 1` a classification loss is computed (Cross-Entropy).

    Returns:
        :obj:`tuple(torch.FloatTensor)` comprising various elements depending on the configuration (:class:`~transformers.BertConfig`) and inputs:
        loss (:obj:`torch.FloatTensor` of shape :obj:`(1,)`, `optional`, returned when :obj:`label` is provided):
            Classification (or regression if config.num_labels==1) loss.
        logits (:obj:`torch.FloatTensor` of shape :obj:`(batch_size, config.num_labels)`):
            Classification (or regression if config.num_labels==1) scores (before SoftMax).
        hidden_states (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_hidden_states=True``):
            Tuple of :obj:`torch.FloatTensor` (one for the output of the embeddings + one for the output of each layer)
            of shape :obj:`(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_attentions=True``):
            Tuple of :obj:`torch.FloatTensor` (one for each layer) of shape
            :obj:`(batch_size, num_heads, sequence_length, sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.

    Examples::

        from transformers import BertTokenizer, BertForSequenceClassification
        import torch

        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertForSequenceClassification.from_pretrained('bert-base-uncased')

        input_ids = torch.tensor(tokenizer.encode("Hello, my dog is cute", add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        labels = torch.tensor([1]).unsqueeze(0)  # Batch size 1
        outputs = model(input_ids, labels=labels)

        loss, logits = outputs[:2]

        """

        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask * NU,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
        )

        pooled_output = outputs[1]

        # Differentially private representation
        pooled_output = self.dropout(pooled_output)
        pooled_output_min = torch.min(pooled_output, dim=-1, keepdims=True)[0]
        pooled_output_max = torch.max(pooled_output, dim=-1, keepdims=True)[0]
        pooled_output = (pooled_output - pooled_output_min) / (
                    pooled_output_max - pooled_output_min)
        pooled_output += noise.view(-1, 1)

        logits = self.classifier(pooled_output)
        # add hidden states and attention if they are here
        outputs = (logits,) + outputs[2:]
        # add hidden states and attention if they are here
        outputs = (logits, pooled_output) + outputs[2:]

        if labels is not None:
            if self.num_labels == 1:
                #  We are doing regression
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1), labels.view(-1))
            else:
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels),
                                labels.view(-1))
            outputs = (loss,) + outputs

        return outputs  # (loss), logits, (hidden_states), (attentions)


class Encoder(BertModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.bert = BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        # self.classifier = nn.Linear(config.hidden_size, self.config.num_labels)
        # self.classifier_proj = nn.Linear(config.projected_dim, self.config.num_labels)

        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            NU=None,
            dp_opts=None,
            # noise=None,
            projection_matrix=None,
    ):
        r"""
        labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size,)`, `optional`, defaults to :obj:`None`):
            Labels for computing the sequence classification/regression loss.
            Indices should be in :obj:`[0, ..., config.num_labels - 1]`.
            If :obj:`config.num_labels == 1` a regression loss is computed (Mean-Square loss),
            If :obj:`config.num_labels > 1` a classification loss is computed (Cross-Entropy).

    Returns:
        :obj:`tuple(torch.FloatTensor)` comprising various elements depending on the configuration (:class:`~transformers.BertConfig`) and inputs:
        loss (:obj:`torch.FloatTensor` of shape :obj:`(1,)`, `optional`, returned when :obj:`label` is provided):
            Classification (or regression if config.num_labels==1) loss.
        logits (:obj:`torch.FloatTensor` of shape :obj:`(batch_size, config.num_labels)`):
            Classification (or regression if config.num_labels==1) scores (before SoftMax).
        hidden_states (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_hidden_states=True``):
            Tuple of :obj:`torch.FloatTensor` (one for the output of the embeddings + one for the output of each layer)
            of shape :obj:`(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_attentions=True``):
            Tuple of :obj:`torch.FloatTensor` (one for each layer) of shape
            :obj:`(batch_size, num_heads, sequence_length, sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.

    Examples::

        from transformers import BertTokenizer, BertForSequenceClassification
        import torch

        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertForSequenceClassification.from_pretrained('bert-base-uncased')

        input_ids = torch.tensor(tokenizer.encode("Hello, my dog is cute", add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        labels = torch.tensor([1]).unsqueeze(0)  # Batch size 1
        outputs = model(input_ids, labels=labels)

        loss, logits = outputs[:2]

        """

        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask * NU,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
        )

        # pooled_output = outputs[1]

        # Differentially private representation
        # pooled_output = self.dropout(pooled_output)
        # pooled_output_min = torch.min(pooled_output, dim=-1, keepdims=True)[0]
        # pooled_output_max = torch.max(pooled_output, dim=-1, keepdims=True)[0]
        # pooled_output = (pooled_output - pooled_output_min) / (
        #             pooled_output_max - pooled_output_min)
        # pooled_output += noise.view(-1, 1)

        # logits = self.classifier(pooled_output)
        # add hidden states and attention if they are here
        # outputs = (logits,) + outputs[2:]
        # add hidden states and attention if they are here
        # outputs = (logits, pooled_output) + outputs[2:]

        # if labels is not None:
        #     if self.num_labels == 1:
        #         #  We are doing regression
        #         loss_fct = MSELoss()
        #         loss = loss_fct(logits.view(-1), labels.view(-1))
        #     else:
        #         loss_fct = CrossEntropyLoss()
        #         loss = loss_fct(logits.view(-1, self.num_labels),
        #                         labels.view(-1))
        #     outputs = (loss,) + outputs

        return outputs  # (loss), logits, (hidden_states), (attentions)


class Classifier(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.classifier = nn.Linear(config.hidden_size, self.config.num_labels)

    def forward(self, inputs):
        pooled_output = self.dropout(inputs)
        pooled_output_min = torch.min(pooled_output, dim=-1, keepdims=True)[0]
        pooled_output_max = torch.max(pooled_output, dim=-1, keepdims=True)[0]
        pooled_output = (pooled_output - pooled_output_min) / (
                    pooled_output_max - pooled_output_min)
        logits = self.classifier(pooled_output)
        return logits


class Attacker(nn.Module):
    def __init__(self, repr_dim, hiddens=256, n_classes=2):
        super().__init__()

        self.proj = nn.Linear(repr_dim, hiddens)
        self.relu = nn.ReLU()
        self.out_proj = nn.Linear(hiddens, n_classes)

    def forward(self, inputs):
        return self.out_proj(self.relu(self.proj(inputs)))


class Attackers(nn.Module):
    def __init__(self, repr_dim, n_attack, hiddens=256, n_classes=2):
        super().__init__()

        self.attackers = nn.ModuleList(
            [Attacker(repr_dim, hiddens, n_classes) for _ in range(n_attack)])

        self.xentropy = nn.CrossEntropyLoss()

    def forward(self, inputs, outputs):
        loss = 0.
        preds = []

        for i, output in enumerate(outputs):
            logits = self.attackers[i](inputs)
            preds.append(torch.argmax(logits, dim=-1))
            loss += self.xentropy(logits, output)

        return loss, preds
