import os
import sys
import argparse
import torch

sys.path.append(os.getcwd())

import src.data.data as data
import src.data.config as cfg
import src.interactive.functions as interactive


def get_atomic_sequence(input_event, model, sampler, data_loader, text_encoder, category):
    if isinstance(category, list):
        outputs = {}
        for cat in category:
            new_outputs = get_atomic_sequence(
                input_event, model, sampler, data_loader, text_encoder, cat)
            outputs.update(new_outputs)
        return outputs
    elif category == "all":
        outputs = {}

        for category in data_loader.categories:
            new_outputs = get_atomic_sequence(
                input_event, model, sampler, data_loader, text_encoder, category)
            outputs.update(new_outputs)
        return outputs
    else:

        sequence_all = {}

        sequence_all["event"] = input_event
        sequence_all["effect_type"] = category

        with torch.no_grad():

            batch = interactive.set_atomic_inputs(
                input_event, category, data_loader, text_encoder)

            sampling_result = sampler.generate_sequence(
                batch, model, data_loader, data_loader.max_event +
                                           data.atomic_data.num_delimiter_tokens["category"],
                                           data_loader.max_effect -
                                           data.atomic_data.num_delimiter_tokens["category"])

        sequence_all['beams'] = sampling_result["beams"]

        #         print_atomic_sequence(sequence_all)

        return {category: sequence_all}


def get_conceptnet_sequence(e1, model, sampler, data_loader, text_encoder, relation, force=False):
    if isinstance(relation, list):
        outputs = {}

        for rel in relation:
            new_outputs = get_conceptnet_sequence(
                e1, model, sampler, data_loader, text_encoder, rel)
            outputs.update(new_outputs)
        return outputs
    elif relation == "all":
        outputs = {}

        for relation in data.conceptnet_data.conceptnet_relations:
            new_outputs = get_conceptnet_sequence(
                e1, model, sampler, data_loader, text_encoder, relation)
            outputs.update(new_outputs)
        return outputs
    else:

        sequence_all = {}

        sequence_all["e1"] = e1
        sequence_all["relation"] = relation

        with torch.no_grad():
            if data_loader.max_r != 1:
                relation_sequence = data.conceptnet_data.split_into_words[relation]
            else:
                relation_sequence = "<{}>".format(relation)

            batch, abort = interactive.set_conceptnet_inputs(
                e1, relation_sequence, text_encoder,
                data_loader.max_e1, data_loader.max_r, force)

            if abort:
                return {relation: sequence_all}

            sampling_result = sampler.generate_sequence(
                batch, model, data_loader,
                data_loader.max_e1 + data_loader.max_r,
                data_loader.max_e2)

        sequence_all['beams'] = sampling_result["beams"]

        # print_conceptnet_sequence(sequence_all)

        return {relation: sequence_all}


def prepare_interaction(model_pretrained, device, data_name):
    model_default = "models/atomic-generation/iteration-500-50000/transformer/categories_oEffect#oReact#oWant#xAttr#xEffect#xIntent#xNeed#xReact#xWant/model_transformer-nL_12-nH_12-hSize_768-edpt_0.1-adpt_0.1-rdpt_0.1-odpt_0.1-pt_gpt-afn_gelu-init_pt-vSize_40542/exp_generation-seed_123-l2_0.01-vl2_T-lrsched_warmup_linear-lrwarm_0.002-clip_1-loss_nll-b2_0.999-b1_0.9-e_1e-08/bs_1-smax_40-sample_greedy-numseq_1-gs_1000-es_1000-categories_oEffect#oReact#oWant#xAttr#xEffect#xIntent#xNeed#xReact#xWant/6.25e-05_adam_64_22000.pickle"
    if os.path.exists(model_pretrained):
        model = model_pretrained
    opt, state_dict = interactive.load_model_file(model)
    data_loader, text_encoder = interactive.load_data(data_name, opt)

    n_ctx = 0

    if data_name == "conceptnet":
        n_ctx = data_loader.max_e1 + data_loader.max_e2 + data_loader.max_r
    else:
        n_ctx = data_loader.max_event + data_loader.max_effect

    n_vocab = len(text_encoder.encoder) + n_ctx
    model = interactive.make_model(opt, n_vocab, n_ctx, state_dict)

    if device != "cpu":
        cfg.device = int(device)
        cfg.do_gpu = True
        torch.cuda.set_device(cfg.device)
        model.cuda(cfg.device)
    else:
        device = "cpu"
    return opt, data_loader, text_encoder, model


if __name__ == '__main__':

    device = 'cpu'
    model_atomic = "pretrained_models/atomic_pretrained_model.pickle"
    model_conceptnet = "pretrained_models/conceptnet_pretrained_model.pickle"

    categories_custom = ['xAttr', 'xEffect', 'xIntent', 'xNeed', 'xReact', 'xWant']
    relation = ['UsedFor', 'IsA']
    sampling_custom = ["greedy", "topk-5"]
    input_event = "start"
    sampling = sampling_custom[0]  # greedy OR topk-NUMBER OR beam-NUMBER

    params = []
    model_dict = {"atomic": model_atomic, "conceptnet": model_conceptnet}
    for data_name, model in model_dict.items():
        params.append(prepare_interaction(model, device, data_name))

    while 1:
        input_event = "help"
        category = "help"
        sampling = "help"
        sampling_algorithm = sampling

        while input_event is None or input_event.lower() == "help":
            input_event = input("Give a command to Pepper : \n")

            if input_event == "help":
                interactive.print_help(opt.dataset)

        #         while sampling_algorithm.lower() == "help":
        #             sampling_algorithm = input("Give a sampling algorithm ")

        sampler_at = interactive.set_sampler(params[0][0], sampling_algorithm, params[0][1])
        sampler_ct = interactive.set_sampler(params[1][0], sampling_algorithm, params[1][1])

        category = categories_custom

        outputs_at = get_atomic_sequence(input_event, params[0][3], sampler_at, params[0][1], params[0][2], category)
        outputs_ct = get_conceptnet_sequence(input_event, params[1][3], sampler_ct, params[1][1], params[1][2],
                                             relation)

        print('Pepper view User as', outputs_at['xAttr']['beams'])
        print('User intends', outputs_at['xIntent']['beams'])
        print('User wants', outputs_at['xWant']['beams'])
        print('User expects Pepper', outputs_at['xNeed']['beams'])
        print("Pepper believes the user's command is to", outputs_ct['UsedFor']['beams'])
        print("Pepper believes the command is", outputs_ct['IsA']['beams'])

        print('\n')

