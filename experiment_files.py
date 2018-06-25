import os

class SceneData:
    def __init__(self, raster_uris=[], ground_truth_label_uri=None, prediction_uri=None):
        self.raster_uris = raster_uris
        self.ground_truth_label_uri = ground_truth_label_uri
        self.prediction_uri = prediction_uri

class ExperimentFiles:
    def __init__(self, training_set={}, validation_set={}, prediction_set={}, class_items={}):
        self.training_set = training_set
        self.validation_set = validation_set
        self.prediction_set = prediction_set
        self.class_items = class_items


    @classmethod
    def from_workflow_config(cls, workflow, rv_root):
        # TODO: Make this more generic, so adding other tasks is easy
        is_classification = workflow['machine_learning']['task'] == 'CLASSIFICATION'
        class_items = workflow['machine_learning']['class_items']

        ground_truth_key = 'classification_geojson_file' \
              if is_classification else 'object_detection_geojson_file'

        training_set = {}
        validation_set = {}
        prediction_set = {}

        # Scenes section -> (dict, has_ground_truth, has_predictions)
        by_section = { 'train_scenes': (training_set, True, False),
                       'test_scenes': (validation_set, True, True),
                       'predict_scenes': (prediction_set, False, True) }

        # Parse workflow information
        for section, (uri_set, has_ground_truth, has_predictions) in by_section.items():
            if section in workflow:
                scene_count = 0
                for scene in workflow[section]:
                    if 'id' in scene:
                        id = scene['id']
                    else:
                        id = "{}_{}".format(section, scene_count)
                    scene_count += 1
                    raster_uris = scene['raster_source']['geotiff_files']['uris']
                    raster_uris = [uri.format(rv_root=rv_root) for uri in raster_uris]

                    if has_ground_truth:
                        ground_truth_label_uri = (scene['ground_truth_label_store']
                                                  [ground_truth_key]['uri'].format(rv_root=rv_root))
                    else:
                        ground_truth_label_uri = None

                    if has_predictions:
                        prediction_labels_uri = os.path.join(
                            rv_root, 'rv-output', 'raw-datasets', workflow['raw_dataset_key'],
                            'datasets', workflow['dataset_key'], 'models', workflow['model_key'],
                            'predictions', workflow['prediction_key'], 'output', id + '.json')
                    else:
                        prediction_labels_uri = None

                    uri_set[id] = SceneData(raster_uris, ground_truth_label_uri, prediction_labels_uri)

        return ExperimentFiles(training_set, validation_set, prediction_set, class_items)
