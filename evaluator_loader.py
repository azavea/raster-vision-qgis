import json

from rastervision.utils.files import file_to_str

from .log import Log

class JsonEvaluatorLoader:
    def load(config, iface):
        if config.output_uri:
            Log.log_info("Evaluation: {}".format(config.evaluator_type))
            eval_data = json.loads(file_to_str(config.output_uri))
            Log.log_info(json.dumps(eval_data, indent=2))
