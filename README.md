# toppingmaker
Package to create parameterized QGIS projects and dump it into a YAML structure.

## Installation
```
pip install toppingmaker
```

## Structure

```
toppingmaker
├── exportsettings.py
├── projecttopping.py
├── target.py
└── utils.py
```

## projecttopping.ProjectTopping
A project configuration resulting in a YAML file that contains:
- layertree
- layerorder
- project variables (future)
- print layout (future)
- map themes (future)

QML style files, QLR layer definition files and the source of a layer can be linked in the YAML file and are exported to the specific folders.

### `parse_project( project: QgsProject, export_settings: ExportSettings = ExportSettings()`
Parses a project into the ProjectTopping structure. Means the LayerTreeNodes are loaded into the layertree variable and append the ExportSettings to each node. The CustomLayerOrder is loaded into the layerorder. The project is not kept as member variable.

### `generate_files(self, target: Target) -> str`
Generates all files according to the passed Target.
The target object containing the paths where to create the files and the path_resolver defining the structure of the link.

### `load_files(self, target: Target)`
not yet implemented

### `generate_project(self, target: Target) -> QgsProject`
not yet implemented

## target.Target
If there is no subdir it will look like:
```
    <maindir>
    ├── projecttopping
    │  └── <projectname>.yaml
    ├── layerstyle
    │  ├── <projectname>_<layername>.qml
    │  └── <projectname>_<layername>.qml
    └── layerdefinition
       └── <projectname>_<layername>.qlr
```
With subdir:
```
    <maindir>
    └── <subdir>
       ├── projecttopping
       │  └── <projectname>.yaml
       ├── layerstyle
       │  ├── <projectname>_<layername>.qml
       │  └── <projectname>_<layername>.qml
       └── layerdefinition
          └── <projectname>_<layername>.qlr
```

The `path_resolver` can be passed as a function. The default implementation lists the created toppingfiles (including the YAML) in the dict `Target.toppingfileinfo_list` with the `"path": <relative_filepath>, "type": <filetype>`.

### `Target( projectname: str = "project", main_dir: str = None, sub_dir: str = None, path_resolver=None)`
The constructor of the target class to set up a target.
A member variable `toppingfileinfo_list = []` is defined, to store all the information according the `path_resolver`.

## exportsettings.ExportSettings

The requested export settings of each node in the specific dicts:
- qmlstyle_setting_nodes
- definition_setting_nodes
- source_setting_nodes

The usual structure is using QgsLayerTreeNode as key and then export True/False

```py
{
    <QgsLayerTreeNode(Node1)>: { export: False }
    <QgsLayerTreeNode(Node2)>: { export: True }
}
```

But alternatively the layername can be used as key. In ProjectTopping it first looks up the node and if not available looking up the name.
Using the node is much more consistent, since one can use layers with the same name, but for nodes you need the project already in advance.
With name you can use prepared settings to pass (before the project exists) e.g. in automated workflows.
```py
{
    "Node1": { export: False }
    "Node2": { export: True }
}
```

For some settings we have additional info. Like in qmlstyle_nodes <QgsMapLayer.StyleCategories>. These are Flags, and can be constructed manually as well.
```py
qmlstyle_nodes =
{
    <QgsLayerTreeNode(Node1)>: { export: False }
    <QgsLayerTreeNode(Node2)>: { export: True, categories: <QgsMapLayer.StyleCategories> }
}
```

### `set_setting_values( type: ToppingType, node: Union[QgsLayerTreeLayer, QgsLayerTreeGroup] = None, name: str = None, export=True categories=None, ) -> bool`

Set the specific types concerning the enumerations:
```py
class ToppingType(Enum):
    QMLSTYLE = 1
    DEFINITION = 2
    SOURCE = 3

```


## User Manual

Having a QGIS Project with some layers:

![QGIS Project Layertree](assets/qgis_project_layertree.png)

### Import the modules

```py
from qgis.core import QgsProject()
from toppingmaker import ProjectTopping, ExportSettings, Target
```

### Create a `ProjectTopping` and parse the QGIS Project

```py
project = QgsProject()
project_topping = ProjectTopping()
project_topping.parse_project(project)
```

This parses the project, but does not yet write the files (only the style and definition file to a temp folder). The QgsProject object is not used anymore.

### Create the `Target`
To write the files we need to define a `Target` object. The target defines where to store the topping files (YAML, style, definition etc.).

```py
target = Target(projectname="freddys_qgis_project", main_dir="/home/fred/repo/", sub_dir="freddys_qgis_topping", pathresover = None)
```

### Generate the Files
```py
project_topping.generate_files(target)
```

Structure looks like this:

```
repo
└── freddys_qgis_topping
    └── projecttopping
        └── freddys_qgis_project.yaml
```

And the YAML looks like this:

```yaml
layerorder: []
layertree:
- Street:
    checked: true
    expanded: true
- Park:
    checked: false
    expanded: true
- Building:
    checked: true
    expanded: true
- Info Layers:
    checked: true
    child-nodes:
    - AssetItem:
        checked: true
        expanded: true
    - InternalProject:
        checked: true
        expanded: true
    expanded: true
    group: true
- Background:
    checked: true
    child-nodes:
    - Landeskarten (grau):
        checked: true
        expanded: true
    expanded: true
    group: true
```

The structure is exported. But not any additional files. For that, we need to parse the `ExportSettings` to the `ProjectTopping`.

### Create the `ExportSettings`:

Use `QMLSTYLE` for the export of the qml stylefile.
Use `DEFINITION` to export the qlr definition file.
USE `SOURCE` to store the source in the YAML tree.

The QgsLayerTreeNode or the layername can be used as key.

```py
export_settings = ExportSettings()
export_settings.set_setting_values(
    type = ExportSettings.ToppingType.QMLSTYLE, node = None, name = "Street", export = True
)
export_settings.set_setting_values(
    type = ExportSettings.ToppingType.SOURCE, node = None, name = "Park", export = True
)
export_settings.set_setting_values(
    type = ExportSettings.ToppingType.DEFINITION, node = None, name = "Info Layers", export = True
)
export_settings.set_setting_values(
    type = ExportSettings.ToppingType.SOURCE, node = None, name = "Landeskarten (grau)", export = True
)
```

Additionally you can pass category flags `QgsMapLayer.StyleCategories` to define what categories needs to be included in the QML Stylefile:

```py
category_flags = QgsMapLayer.StyleCategory.AllStyleCategories

export_settings.set_setting_values(
    type = ExportSettings.ToppingType.QMLSTYLE, node = None, name = "Street", export = True, categories = category_flags
)
```

### Generate the Files for a `ProjectTopping` containing `ExportSetting`
When parsing the QgsProject we need to pass the `ExportSettings`:
```

project_topping.parse_project(project, export_settings)
project_topping.generate_files(target)
```

Structure looks like this:

```
repo
└── freddys_qgis_topping
    ├── layerdefinition
    │   └── freddys_qgis_project_info_layers.qlr
    └── projecttopping
        └── freddys_qgis_project.yaml
    └── layerstyle
        └── freddys_qgis_project_street.qml
```

And the YAML looks like this:

```yaml
layerorder: []
layertree:
- Street:
    checked: true
    expanded: true
    stylefile: freddys_qgis_topping/layerstyle/freddys_qgis_project_street.qml
- Park:
    checked: false
    expanded: true
    provider: ogr
    uri: /home/freddy/qgis_projects/bakery/cityandcity.gpkg|layername=park
- Building:
    checked: true
    expanded: true
- Info Layers:
    checked: true
    definitionfile: freddys_qgis_topping/layerdefinition/freddys_qgis_project_info_layers.qlr
    expanded: true
    group: true
- Background:
    checked: true
    child-nodes:
    expanded: true
    group: true
    - Landeskarten (grau):
        checked: true
        expanded: true
        provider: wms
        uri: contextualWMSLegend=0&crs=EPSG:2056&dpiMode=7&featureCount=10&format=image/jpeg&layers=ch.swisstopo.pixelkarte-grau&styles&url=https://wms.geo.admin.ch/?%0ASERVICE%3DWMS%0A%26VERSION%3D1.3.0%0A%26REQUEST%3DGetCapabilities
```

## Infos for Devs

### Code style

Is enforced with pre-commit. To use, make:
```
pip install pre-commit
pre-commit install
```
And to run it over all the files (with infile changes):
```
pre-commit run --color=always --all-file
```
