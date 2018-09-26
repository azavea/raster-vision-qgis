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
                 name,
                 image_sld = "",
                 ground_truth_sld = "",
                 prediction_sld = "",
                 aoi_sld = ""):
        self.name = name
        self.image_sld = image_sld
        self.ground_truth_sld = ground_truth_sld
        self.prediction_sld = prediction_sld
        self.aoi_sld = aoi_sld

    def to_json_str(self):
        return json.dumps({ 'name': self.name,
                            'image_sld': self.image_sld,
                            'ground_truth_sld': self.ground_truth_sld,
                            'prediction_sld': self.prediction_sld,
                            'aoi_sld': self.aoi_sld })


    @classmethod
    def from_json_str(cls, json_str):
        js = json.loads(json_str)
        name = js['name']
        try:
            return StyleProfile(name,
                                js['image_sld'],
                                js['ground_truth_sld'],
                                js['prediction_sld'],
                                js['aoi_sld'])
        except KeyError:
            return StyleProfile(name)

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

    # Experiment config URI
    def get_experiment_uri(self):
        return self.settings.value("experiment/experiment_uri", "")

    def set_experiment_uri(self, v):
        self.settings.setValue("experiment/experiment_uri", v)

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
        return self.settings.value('profiles/index', 0, int)

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
