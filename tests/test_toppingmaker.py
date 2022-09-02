import datetime
import logging
import os
import tempfile

import yaml
from qgis.core import QgsProject, QgsVectorLayer
from qgis.testing import unittest

from toppingmaker import ExportSettings, ProjectTopping, Target


class ToppingMakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run before all tests."""
        cls.basetestpath = tempfile.mkdtemp()
        cls.projecttopping_test_path = os.path.join(cls.basetestpath, "projecttopping")

    def test_target(self):
        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"
        filedirs = ["projecttopping", "layerstyle", "layerdefinition", "andanotherone"]
        target = Target("freddys", maindir, subdir)
        count = 0
        for filedir in filedirs:
            # filedir_path should create the dir
            path, _ = target.filedir_path(filedir)
            assert os.path.isdir(path)
            count += 1
        assert count == 4

    def test_parse_project(self):
        """
        "Big Group":
            group: True
            child-nodes:
                - "Layer One":
                    checked: True
                - "Medium Group":
                    group: True
                    child-nodes:
                        - "Layer Two":
                        - "Small Group:
                            - "Layer Three":
                            - "Layer Four":
                        - "Layer Five":
        "All of em":
            group: True
            child-nodes:
                - "Layer One":
                    checked: False
                - "Layer Two":
                - "Layer Three":
                    checked: False
                - "Layer Four":
                - "Layer Five":
        """
        project, _ = self._make_project_and_export_settings()
        layers = project.layerTreeRoot().findLayers()
        self.assertEqual(len(layers), 10)

        project_topping = ProjectTopping()
        project_topping.parse_project(project)

        checked_groups = []
        for item in project_topping.layertree.items:
            if item.name == "Big Group":
                assert len(item.items) == 2
                checked_groups.append("Big Group")
                for item in item.items:
                    if item.name == "Medium Group":
                        assert len(item.items) == 3
                        checked_groups.append("Medium Group")
                        for item in item.items:
                            if item.name == "Small Group":
                                assert len(item.items) == 2
                                checked_groups.append("Small Group")
        assert checked_groups == ["Big Group", "Medium Group", "Small Group"]

    def test_generate_files(self):
        project, export_settings = self._make_project_and_export_settings()
        layers = project.layerTreeRoot().findLayers()
        self.assertEqual(len(layers), 10)

        project_topping = ProjectTopping()
        project_topping.parse_project(project, export_settings)

        checked_groups = []
        for item in project_topping.layertree.items:
            if item.name == "Big Group":
                assert len(item.items) == 2
                checked_groups.append("Big Group")
                for item in item.items:
                    if item.name == "Medium Group":
                        assert len(item.items) == 3
                        checked_groups.append("Medium Group")
                        for item in item.items:
                            if item.name == "Small Group":
                                assert len(item.items) == 2
                                checked_groups.append("Small Group")
        assert checked_groups == ["Big Group", "Medium Group", "Small Group"]

        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = Target("freddys", maindir, subdir)

        projecttopping_file_path = os.path.join(
            target.main_dir, project_topping.generate_files(target)
        )

        # check projecttopping_file
        foundAllofEm = False
        foundLayerOne = False
        foundLayerTwo = False

        with open(projecttopping_file_path, "r") as yamlfile:
            projecttopping_data = yaml.safe_load(yamlfile)
            assert "layertree" in projecttopping_data
            assert projecttopping_data["layertree"]
            for node in projecttopping_data["layertree"]:
                if "All of em" in node:
                    foundAllofEm = True
                    assert "child-nodes" in node["All of em"]
                    for childnode in node["All of em"]["child-nodes"]:
                        if "Layer One" in childnode:
                            foundLayerOne = True
                            assert "checked" in childnode["Layer One"]
                            assert not childnode["Layer One"]["checked"]
                        if "Layer Two" in childnode:
                            foundLayerTwo = True
                            assert "checked" in childnode["Layer Two"]
                            assert childnode["Layer Two"]["checked"]
        assert foundAllofEm
        assert foundLayerOne
        assert foundLayerTwo

        # check toppingfiles

        # there should be exported 6 files (see _make_project_and_export_settings)
        # stylefiles:
        # "Layer One"
        # "Layer Three"
        # "Layer Five"
        #
        # definitionfiles:
        # "Layer Three"
        # "Layer Four"
        # "Layer Five"

        countchecked = 0

        # there should be 13 toppingfiles: one project topping, and 2 x 6 toppingfiles of the layers (since the layers are multiple times in the tree)
        assert len(target.toppingfileinfo_list) == 13

        for toppingfileinfo in target.toppingfileinfo_list:
            assert "path" in toppingfileinfo
            assert "type" in toppingfileinfo

            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerstyle/freddys_layer_one.qml"
            ):
                countchecked += 1
            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerstyle/freddys_layer_three.qml"
            ):
                countchecked += 1
            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerstyle/freddys_layer_five.qml"
            ):
                countchecked += 1
            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerdefinition/freddys_layer_three.qlr"
            ):
                countchecked += 1
            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerdefinition/freddys_layer_four.qlr"
            ):
                countchecked += 1
            if (
                toppingfileinfo["path"]
                == "freddys_projects/this_specific_project/layerdefinition/freddys_layer_five.qlr"
            ):
                countchecked += 1

        assert countchecked == 12

    def test_custom_path_resolver(self):
        # load QGIS project into structure
        project_topping = ProjectTopping()
        project, export_settings = self._make_project_and_export_settings()
        project_topping.parse_project(project, export_settings)

        # create target with path resolver
        maindir = os.path.join(self.projecttopping_test_path, "freddys_repository")
        subdir = "freddys_projects/this_specific_project"

        target = Target("freddys", maindir, subdir, custom_path_resolver)

        project_topping.generate_files(target)

        # there should be exported 6 files (see _make_project_and_export_settings)
        # stylefiles:
        # "Layer One"
        # "Layer Three"
        # "Layer Five"
        #
        # definitionfiles:
        # "Layer Three"
        # "Layer Four"
        # "Layer Five"

        countchecked = 0
        for toppingfileinfo in target.toppingfileinfo_list:
            assert "id" in toppingfileinfo
            assert "path" in toppingfileinfo
            assert "type" in toppingfileinfo
            assert "version" in toppingfileinfo

            if toppingfileinfo["id"] == "layerstyle_freddys_layer_one.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "layerstyle_freddys_layer_three.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "layerstyle_freddys_layer_five.qml_001":
                countchecked += 1
            if toppingfileinfo["id"] == "layerdefinition_freddys_layer_three.qlr_001":
                countchecked += 1
            if toppingfileinfo["id"] == "layerdefinition_freddys_layer_four.qlr_001":
                countchecked += 1
            if toppingfileinfo["id"] == "layerdefinition_freddys_layer_five.qlr_001":
                countchecked += 1

        assert countchecked == 6

    def _make_project_and_export_settings(self):
        project = QgsProject()
        project.removeAllMapLayers()

        l1 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer One", "memory"
        )
        assert l1.isValid()
        l2 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Two", "memory"
        )
        assert l2.isValid()
        l3 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Three", "memory"
        )
        assert l3.isValid()
        l4 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Four", "memory"
        )
        assert l4.isValid()
        l5 = QgsVectorLayer(
            "point?crs=epsg:4326&field=id:integer", "Layer Five", "memory"
        )
        assert l5.isValid()

        project.addMapLayer(l1, False)
        project.addMapLayer(l2, False)
        project.addMapLayer(l3, False)
        project.addMapLayer(l4, False)
        project.addMapLayer(l5, False)

        biggroup = project.layerTreeRoot().addGroup("Big Group")
        biggroup.addLayer(l1)
        mediumgroup = biggroup.addGroup("Medium Group")
        mediumgroup.addLayer(l2)
        smallgroup = mediumgroup.addGroup("Small Group")
        smallgroup.addLayer(l3)
        smallgroup.addLayer(l4)
        mediumgroup.addLayer(l5)
        allofemgroup = project.layerTreeRoot().addGroup("All of em")
        node1 = allofemgroup.addLayer(l1)
        node1.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l2)
        node3 = allofemgroup.addLayer(l3)
        node3.setItemVisibilityChecked(False)
        allofemgroup.addLayer(l4)
        allofemgroup.addLayer(l5)

        export_settings = ExportSettings()
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE, None, "Layer One", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE, None, "Layer Three", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.QMLSTYLE, None, "Layer Five", True
        )

        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Three", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Four", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.DEFINITION, None, "Layer Five", True
        )

        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Layer One", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Layer Two", True
        )
        export_settings.set_setting_values(
            ExportSettings.ToppingType.SOURCE, None, "Layer Three", True
        )

        print(export_settings.qmlstyle_setting_nodes)
        print(export_settings.definition_setting_nodes)
        print(export_settings.source_setting_nodes)
        return project, export_settings

    def print_info(self, text):
        logging.info(text)

    def print_error(self, text):
        logging.error(text)


def custom_path_resolver(target: Target, name, type):
    _, relative_filedir_path = target.filedir_path(type)
    id = unique_id_in_target_scope(target, f"{type}_{name}_001")
    path = os.path.join(relative_filedir_path, name)
    type = type
    version = datetime.datetime.now().strftime("%Y-%m-%d")
    toppingfile = {"id": id, "path": path, "type": type, "version": version}
    target.toppingfileinfo_list.append(toppingfile)
    return path


def unique_id_in_target_scope(target: Target, id):
    for toppingfileinfo in target.toppingfileinfo_list:
        if "id" in toppingfileinfo and toppingfileinfo["id"] == id:
            iterator = int(id[-3:])
            iterator += 1
            id = f"{id[:-3]}{iterator:03}"
            return unique_id_in_target_scope(target, id)
    return id
