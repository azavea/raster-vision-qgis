import os
import json

from PyQt5.QtCore import QSettings

from .viz_workflow import ExperimentLoadOptions

class InfoUrls:
    def __init__(self):
        self.experiment = "http://github.com/azavea/raster-vision"
        self.predict = "http://github.com/azavea/raster-vision"
        self.profiles = "http://github.com/azavea/raster-vision"
        self.config = "http://github.com/azavea/raster-vision"

class StyleProfile:
    def __init__(self,
                 name, training_scenes_sld = "", training_labels_sld = "",
                 validation_scenes_sld = "", validation_labels_sld = "", validation_predictions_sld = "",
                 prediction_scenes_sld = "", predictions_sld = ""):
        self.name = name
        self.training_scenes_sld = training_scenes_sld
        self.training_labels_sld = training_labels_sld
        self.validation_scenes_sld = validation_scenes_sld
        self.validation_labels_sld = validation_labels_sld
        self.validation_predictions_sld = validation_predictions_sld
        self.prediction_scenes_sld = prediction_scenes_sld
        self.predictions_sld = predictions_sld

    def to_json_str(self):
        return json.dumps({ 'name': self.name,
                            'training_scenes_sld': self.training_scenes_sld,
                            'training_labels_sld': self.training_labels_sld,
                            'validation_scenes_sld': self.validation_scenes_sld,
                            'validation_labels_sld': self.validation_labels_sld,
                            'validation_predictions_sld': self.validation_predictions_sld,
                            'prediction_scenes_sld': self.prediction_scenes_sld,
                            'predictions_sld': self.predictions_sld })


    @classmethod
    def from_json_str(cls, json_str):
        js = json.loads(json_str)
        return StyleProfile(js['name'], js['training_scenes_sld'],
                            js['training_labels_sld'], js['validation_scenes_sld'],
                            js['validation_labels_sld'], js['validation_predictions_sld'],
                            js['prediction_scenes_sld'], js['predictions_sld'])

    @classmethod
    def EMPTY(cls):
        return StyleProfile("(None)")

class Settings(object):
    def __init__(self):
        self.settings = QSettings(QSettings.IniFormat,
                                  QSettings.UserScope,
                                  'Azavea', 'RasterVision')

    def get_default_working_dir(self):
        home = os.path.expanduser("~")
        d = os.path.join(home, ".qgis/plugins/raster-vision/working-dir")
        if not os.path.exists(d):
            os.makedirs(d)
        return d

    ### Load Experiment

    # Raster Vision Root
    def get_rv_root(self):
        return self.settings.value("experiment/rv_root", "")

    def set_rv_root(self, v):
        self.settings.setValue("experiment/rv_root", v)

    # Workflow URI
    def get_workflow_uri(self):
        return self.settings.value("experiment/workflow_uri", "")

    def set_workflow_uri(self, v):
        self.settings.setValue("experiment/workflow_uri", v)

    # Experiment style profile
    def get_experiment_profile(self):
        return self.settings.value('experiment/profile', "")

    def set_experiment_profile(self, v):
        self.settings.setValue('experiment/profile', v)

    # Experiment load options
    def get_experiment_load_options(self):
        s = self.settings.value("experiment/experiment_load_options")
        if s:
            return ExperimentLoadOptions.from_json(json.loads(s))
        else:
            return ExperimentLoadOptions()

    def set_experiment_load_options(self, v):
        self.settings.setValue("experiment/experiment_load_options", json.dumps(v.to_json()))

    ### Predict

    # Raster Vision Model File
    def get_model_file(self):
        return self.settings.value("predict/model_file", "")

    def set_model_file(self, v):
        self.settings.setValue("predict/model_file", v)

    # Predict style profile
    def get_predict_profile(self):
        return self.settings.value('predict/profile', "")

    def set_predict_profile(self, v):
        self.settings.setValue('predict/profile', v)

    ### Style Profiles

    # Style profiles
    def get_style_profiles(self):
        return list(map(StyleProfile.from_json_str, self.settings.value('profiles/profile_list', [], str)))

    def set_style_profiles(self, v):
        self.settings.setValue('profiles/profile_list', list(map(lambda x: x.to_json_str(), v)))

    # Style profiles index
    def get_style_profiles_index(self):
        return self.settings.value('profiles/index', 0)

    def set_style_profiles_index(self, v):
        self.settings.setValue('profiles/index', v)

    ### Configuration

    # Working Directory
    def get_working_dir(self):
        return self.settings.value("config/working_dir", self.get_default_working_dir())

    def set_working_dir(self, v):
        self.settings.setValue("config/working_dir", v)

    # AWS Profile
    def get_aws_profile(self):
        return self.settings.value("config/aws_profile", None)

    def set_aws_profile(self, v):
        self.settings.setValue("config/aws_profile", v)
