# -*- coding: utf-8 -*-
"""Developer convenience functions for ibs (detections).

TODO: need to split up into sub modules:
    consistency_checks
    feasibility_fixes
    move the export stuff to dbio

    then there are also convineience functions that need to be ordered at least
    within this file
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from ibeis.control import controller_inject
from os.path import join, exists
import utool as ut

# Inject utool functions
(print, rrr, profile) = ut.inject2(__name__, '[other.detecttrain]')


CLASS_INJECT_KEY, register_ibs_method = (
    controller_inject.make_ibs_register_decorator(__name__))


@register_ibs_method
def classifier_cameratrap_train(ibs, positive_imageset_id, negative_imageset_id, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_classifier_cameratrap_binary_training_images
    from ibeis_cnn.process import numpy_processed_directory2
    from ibeis_cnn.models.classifier import train_classifier
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_cnn_classifier_cameratrap_binary_training_images(ibs,
                                                                          positive_imageset_id,
                                                                          negative_imageset_id,
                                                                          dest_path=data_path,
                                                                          **kwargs)
    id_file, X_file, y_file = numpy_processed_directory2(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'classifier-cameratrap')
    model_path = train_classifier(output_path, X_file, y_file)
    # Return model path
    return model_path


@register_ibs_method
def classifier_cameratrap_densenet_train(ibs, positive_imageset_id, negative_imageset_id,
                                         ensembles=3, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_classifier_cameratrap_binary_training_images_pytorch
    from ibeis.algo.detect import densenet

    data_path = join(ibs.get_cachedir(), 'extracted-classifier-cameratrap')
    extracted_path = get_cnn_classifier_cameratrap_binary_training_images_pytorch(
        ibs,
        positive_imageset_id,
        negative_imageset_id,
        dest_path=data_path,
        image_size=densenet.INPUT_SIZE,
        **kwargs
    )

    weights_path_list = []
    for ensemble_num in range(ensembles):
        args = (ensemble_num, )
        output_path = join(ibs.get_cachedir(), 'training', 'classifier-cameratrap-ensemble-%d' % args)
        weights_path = densenet.train(extracted_path, output_path, blur=True, flip=True)
        weights_path_list.append(weights_path)

    archive_name = 'classifier.cameratrap.zip'
    archive_path = join(ibs.get_cachedir(), 'training', archive_name)
    ensemble_weights_path_list = []

    for index, weights_path in enumerate(sorted(weights_path_list)):
        assert exists(weights_path)
        ensemble_weights_path = 'classifier.cameratrap.%d.weights' % (index, )
        ut.copy(weights_path, ensemble_weights_path)
        ensemble_weights_path_list.append(ensemble_weights_path)

    ut.archive_files(archive_path, ensemble_weights_path_list, overwrite=True, common_prefix=True)

    return archive_path


@register_ibs_method
def classifier_binary_train(ibs, species_list, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_classifier_binary_training_images
    from ibeis_cnn.process import numpy_processed_directory2
    from ibeis_cnn.models.classifier import train_classifier
    from ibeis_cnn.utils import save_model
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_cnn_classifier_binary_training_images(ibs, species_list,
                                                               dest_path=data_path,
                                                               **kwargs)
    id_file, X_file, y_file = numpy_processed_directory2(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'classifier-binary')
    model_path = train_classifier(output_path, X_file, y_file)
    # Add the species_list to the model
    model_state = ut.load_cPkl(model_path)
    assert 'species_list' not in model_state
    model_state['species_list'] = species_list
    save_model(model_state, model_path)
    # Return model path
    return model_path


@register_ibs_method
def classifier2_train(ibs, species_list=None, species_mapping={}, train_gid_set=None, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_classifier2_training_images
    from ibeis_cnn.process import numpy_processed_directory3
    from ibeis_cnn.models.classifier2 import train_classifier2
    from ibeis_cnn.utils import save_model
    if species_list is not None:
        species_list = sorted(species_list)
    data_path = join(ibs.get_cachedir(), 'extracted')
    values = get_cnn_classifier2_training_images(ibs, species_list,
                                                 category_mapping=species_mapping,
                                                 train_gid_set=train_gid_set,
                                                 dest_path=data_path,
                                                 **kwargs)
    extracted_path, category_list = values
    id_file, X_file, y_file = numpy_processed_directory3(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'classifier2')
    model_path = train_classifier2(output_path, X_file, y_file, purge=True)
    # Add the species_list to the model
    model_state = ut.load_cPkl(model_path)
    assert 'category_list' not in model_state
    model_state['category_list'] = category_list
    save_model(model_state, model_path)
    # Return model path
    return model_path


@register_ibs_method
def classifier_train(ibs, **kwargs):
    return ibs.classifier2_train(**kwargs)


@register_ibs_method
def canonical_classifier_train(ibs, species, ensembles=3, extracted_path=None, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_classifier_canonical_training_images_pytorch
    from ibeis.algo.detect import densenet

    args = (species, )
    data_path = join(ibs.get_cachedir(), 'extracted-classifier-canonical-%s' % args)
    if extracted_path is None:
        extracted_path = get_cnn_classifier_canonical_training_images_pytorch(
            ibs,
            species,
            dest_path=data_path,
        )

    weights_path_list = []
    for ensemble_num in range(ensembles):
        args = (species, ensemble_num, )
        output_path = join(ibs.get_cachedir(), 'training', 'classifier-canonical-%s-ensemble-%d' % args)
        if exists(output_path):
            ut.delete(output_path)
        weights_path = densenet.train(extracted_path, output_path, blur=False, flip=False)
        weights_path_list.append(weights_path)

    args = (species, )
    output_name = 'classifier.canonical.%s' % args
    ensemble_path = join(ibs.get_cachedir(), 'training', output_name)
    ut.ensuredir(ensemble_path)

    archive_path = '%s.zip' % (ensemble_path)
    ensemble_weights_path_list = []

    for index, weights_path in enumerate(sorted(weights_path_list)):
        assert exists(weights_path)
        ensemble_weights_path = join(ensemble_path, 'classifier.canonical.%d.weights' % (index, ))
        ut.copy(weights_path, ensemble_weights_path)
        ensemble_weights_path_list.append(ensemble_weights_path)

    ensemble_weights_path_list = [ensemble_path] + ensemble_weights_path_list
    ut.archive_files(archive_path, ensemble_weights_path_list, overwrite=True, common_prefix=True)

    return archive_path


@register_ibs_method
def canonical_localizer_train(ibs, species, ensembles=3, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_localizer_canonical_training_images_pytorch
    from ibeis.algo.detect import canonical

    args = (species, )
    data_path = join(ibs.get_cachedir(), 'extracted-localizer-canonical-%s' % args)
    extracted_path = get_cnn_localizer_canonical_training_images_pytorch(
        ibs,
        species,
        dest_path=data_path,
    )

    weights_path_list = []
    for ensemble_num in range(ensembles):
        args = (species, ensemble_num, )
        output_path = join(ibs.get_cachedir(), 'training', 'localizer-canonical-%s-ensemble-%d' % args)
        weights_path = canonical.train(extracted_path, output_path)
        weights_path_list.append(weights_path)

    args = (species, )
    output_name = 'localizer.canonical.%s' % args
    ensemble_path = join(ibs.get_cachedir(), 'training', output_name)
    ut.ensuredir(ensemble_path)

    archive_path = '%s.zip' % (ensemble_path)
    ensemble_weights_path_list = []

    for index, weights_path in enumerate(sorted(weights_path_list)):
        assert exists(weights_path)
        ensemble_weights_path = join(ensemble_path, 'localizer.canonical.%d.weights' % (index, ))
        ut.copy(weights_path, ensemble_weights_path)
        ensemble_weights_path_list.append(ensemble_weights_path)

    ensemble_weights_path_list = [ensemble_path] + ensemble_weights_path_list
    ut.archive_files(archive_path, ensemble_weights_path_list, overwrite=True, common_prefix=True)

    return archive_path


@register_ibs_method
def localizer_yolo_train(ibs, species_list=None, **kwargs):
    from pydarknet import Darknet_YOLO_Detector
    data_path = ibs.export_to_xml(species_list=species_list, **kwargs)
    output_path = join(ibs.get_cachedir(), 'training', 'localizer')
    ut.ensuredir(output_path)
    dark = Darknet_YOLO_Detector()
    model_path = dark.train(data_path, output_path)
    del dark
    return model_path


def _localizer_lightnet_validate_training_kit(lightnet_training_kit_url):
    # Remove bad files
    delete_path_list = [
        join(lightnet_training_kit_url, '__MACOSX'),
    ]
    for delete_path in delete_path_list:
        if exists(delete_path):
            ut.delete(delete_path)

    # Ensure first-level structure
    bin_path     = join(lightnet_training_kit_url, 'bin')
    cfg_path     = join(lightnet_training_kit_url, 'cfg')
    data_path    = join(lightnet_training_kit_url, 'data')
    weights_path = join(lightnet_training_kit_url, 'darknet19_448.conv.23.pt')
    assert exists(bin_path)
    assert exists(cfg_path)
    assert exists(data_path)
    assert exists(weights_path)

    # Ensure second-level structure
    dataset_py_path = join(bin_path, 'dataset.template.py')
    labels_py_path  = join(bin_path, 'labels.template.py')
    test_py_path    = join(bin_path, 'test.template.py')
    train_py_path   = join(bin_path, 'train.template.py')
    config_py_path  = join(cfg_path, 'yolo.template.py')
    assert exists(dataset_py_path)
    assert exists(labels_py_path)
    assert exists(test_py_path)
    assert exists(train_py_path)
    assert exists(config_py_path)


def _localizer_lightnet_template_replace(template_filepath, replace_dict, output_filepath=None):
    if output_filepath is None:
        output_filepath = template_filepath.replace('.template.', '.')
    with open(template_filepath, 'r') as template_file:
        template = ''.join(template_file.readlines())
    for search_str, replace_str in replace_dict.items():
        search_str  = str(search_str)
        replace_str = str(replace_str)
        template = template.replace(search_str, replace_str)
    with open(output_filepath, 'w') as output_file:
        output_file.write(template)
    return output_filepath


@register_ibs_method
def localizer_lightnet_train(ibs, species_list, cuda_device=0, batches=60000, **kwargs):
    from ibeis.algo.detect import lightnet
    import subprocess
    import datetime
    import sys

    assert species_list is not None
    species_list = sorted(species_list)

    lightnet_training_kit_url = lightnet._download_training_kit()
    _localizer_lightnet_validate_training_kit(lightnet_training_kit_url)

    hashstr = ut.random_nonce()[:16]
    species_str = '-'.join(species_list)

    cache_path = join(ibs.cachedir, 'training', 'lightnet')
    ut.ensuredir(cache_path)
    training_instance_folder = 'lightnet-training-%s-%s' % (species_str, hashstr, )
    training_instance_path = join(cache_path, training_instance_folder)
    ut.copy(lightnet_training_kit_url, training_instance_path)

    backup_path     = join(training_instance_path, 'backup')
    bin_path        = join(training_instance_path, 'bin')
    cfg_path        = join(training_instance_path, 'cfg')
    data_path       = join(training_instance_path, 'data')
    weights_path    = join(training_instance_path, 'darknet19_448.conv.23.pt')
    results_path    = join(training_instance_path, 'results.txt')
    dataset_py_path = join(bin_path, 'dataset.template.py')
    labels_py_path  = join(bin_path, 'labels.template.py')
    test_py_path    = join(bin_path, 'test.template.py')
    train_py_path   = join(bin_path, 'train.template.py')
    config_py_path  = join(cfg_path, 'yolo.template.py')

    ibs.export_to_xml(species_list=species_list, output_path=data_path, **kwargs)

    species_str_list = ['%r' % (species, ) for species in species_list]
    species_str = ', '.join(species_str_list)
    replace_dict = {
        '_^_YEAR_^_'            : str(datetime.datetime.now().year),
        '_^_DATA_ROOT_^_'       : data_path,
        '_^_SPECIES_MAPPING_^_' : species_str,
        '_^_NUM_BATCHES_^_'     : str(batches),
    }

    dataset_py_path = _localizer_lightnet_template_replace(dataset_py_path, replace_dict)
    labels_py_path  = _localizer_lightnet_template_replace(labels_py_path,  replace_dict)
    test_py_path    = _localizer_lightnet_template_replace(test_py_path,    replace_dict)
    train_py_path   = _localizer_lightnet_template_replace(train_py_path,   replace_dict)
    config_py_path  = _localizer_lightnet_template_replace(config_py_path,  replace_dict)
    assert exists(dataset_py_path)
    assert exists(labels_py_path)
    assert exists(test_py_path)
    assert exists(train_py_path)
    assert exists(config_py_path)
    assert not exists(backup_path)
    assert not exists(results_path)

    python_exe = sys.executable

    # Call labels
    call_str = '%s %s' % (python_exe, labels_py_path, )
    print(call_str)
    subprocess.call(call_str, shell=True)

    # Call training
    # Example: CUDA_VISIBLE_DEVICES=0 python bin/train.py -c -n cfg/yolo.py -c darknet19_448.conv.23.pt
    cuda_str = '' if cuda_device in [-1, None] else 'CUDA_VISIBLE_DEVICES=%s ' % (cuda_device, )
    args = (cuda_str, python_exe, train_py_path, config_py_path, backup_path, weights_path)
    call_str = '%s%s %s -c -n %s -b %s %s' % args
    print(call_str)
    subprocess.call(call_str, shell=True)
    assert exists(backup_path)

    # Call testing
    # Example: CUDA_VISIBLE_DEVICE=0 python bin/test.py -c -n cfg/yolo.py
    cuda_str = '' if cuda_device in [-1, None] else 'CUDA_VISIBLE_DEVICES=%s ' % (cuda_device, )
    args = (cuda_str, python_exe, test_py_path, config_py_path, backup_path, )
    call_str = '%s%s %s -c -n %s --results results.txt %s/*' % args
    print(call_str)
    subprocess.call(call_str, shell=True)
    assert exists(results_path)


@register_ibs_method
def labeler_train_ibeis_cnn(ibs, species_list=None, species_mapping=None, viewpoint_mapping=None, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_labeler_training_images
    from ibeis_cnn.process import numpy_processed_directory2
    from ibeis_cnn.models.labeler import train_labeler
    from ibeis_cnn.utils import save_model
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_cnn_labeler_training_images(ibs, data_path,
                                                     category_list=species_list,
                                                     category_mapping=species_mapping,
                                                     viewpoint_mapping=viewpoint_mapping,
                                                     **kwargs)
    id_file, X_file, y_file = numpy_processed_directory2(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'labeler')
    model_path = train_labeler(output_path, X_file, y_file)
    # Add the species_list to the model
    model_state = ut.load_cPkl(model_path)
    assert 'category_list' not in model_state
    model_state['category_list'] = species_list
    assert 'viewpoint_mapping' not in model_state
    model_state['viewpoint_mapping'] = viewpoint_mapping
    save_model(model_state, model_path)
    return model_path


@register_ibs_method
def labeler_train(ibs, species_list=None, species_mapping=None, viewpoint_mapping=None, ensembles=3, **kwargs):
    from ibeis_cnn.ingest_ibeis import get_cnn_labeler_training_images_pytorch
    from ibeis.algo.detect import densenet

    species = '-'.join(species_list)
    args = (species, )
    data_path = join(ibs.get_cachedir(), 'extracted-labeler-%s' % args)
    extracted_path = get_cnn_labeler_training_images_pytorch(
        ibs,
        category_list=species_list,
        category_mapping=species_mapping,
        viewpoint_mapping=viewpoint_mapping,
        dest_path=data_path,
        **kwargs
    )

    weights_path_list = []
    for ensemble_num in range(ensembles):
        args = (species, ensemble_num, )
        output_path = join(ibs.get_cachedir(), 'training', 'labeler-%s-ensemble-%d' % args)
        if exists(output_path):
            ut.delete(output_path)
        weights_path = densenet.train(extracted_path, output_path, blur=False, flip=False)
        weights_path_list.append(weights_path)

    args = (species, )
    output_name = 'labeler.%s' % args
    ensemble_path = join(ibs.get_cachedir(), 'training', output_name)
    ut.ensuredir(ensemble_path)

    archive_path = '%s.zip' % (ensemble_path)
    ensemble_weights_path_list = []

    for index, weights_path in enumerate(sorted(weights_path_list)):
        assert exists(weights_path)
        ensemble_weights_path = join(ensemble_path, 'labeler.%d.weights' % (index, ))
        ut.copy(weights_path, ensemble_weights_path)
        ensemble_weights_path_list.append(ensemble_weights_path)

    ensemble_weights_path_list = [ensemble_path] + ensemble_weights_path_list
    ut.archive_files(archive_path, ensemble_weights_path_list, overwrite=True, common_prefix=True)

    return archive_path


# @register_ibs_method
# def qualifier_train(ibs, **kwargs):
#     from ibeis_cnn.ingest_ibeis import get_cnn_qualifier_training_images
#     from ibeis_cnn.process import numpy_processed_directory2
#     from ibeis_cnn.models.qualifier import train_qualifier
#     data_path = join(ibs.get_cachedir(), 'extracted')
#     extracted_path = get_cnn_qualifier_training_images(ibs, data_path, **kwargs)
#     id_file, X_file, y_file = numpy_processed_directory2(extracted_path)
#     output_path = join(ibs.get_cachedir(), 'training', 'qualifier')
#     model_path = train_qualifier(output_path, X_file, y_file)
#     return model_path


@register_ibs_method
def detector_train(ibs):
    results = ibs.localizer_yolo_train()
    localizer_weight_path, localizer_config_path, localizer_class_path = results
    classifier_model_path = ibs.classifier_binary_train()
    labeler_model_path = ibs.labeler_train()
    output_path = join(ibs.get_cachedir(), 'training', 'detector')
    ut.ensuredir(output_path)
    ut.copy(localizer_weight_path, join(output_path, 'localizer.weights'))
    ut.copy(localizer_config_path, join(output_path, 'localizer.config'))
    ut.copy(localizer_class_path,  join(output_path, 'localizer.classes'))
    ut.copy(classifier_model_path, join(output_path, 'classifier.npy'))
    ut.copy(labeler_model_path,    join(output_path, 'labeler.npy'))


@register_ibs_method
def background_train(ibs, species):
    from ibeis_cnn.ingest_ibeis import get_background_training_patches2
    from ibeis_cnn.process import numpy_processed_directory2
    from ibeis_cnn.models.background import train_background
    from ibeis_cnn.utils import save_model
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_background_training_patches2(ibs, species, data_path,
                                                      patch_size=50,
                                                      global_limit=500000)
    id_file, X_file, y_file = numpy_processed_directory2(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'background')
    model_path = train_background(output_path, X_file, y_file)
    model_state = ut.load_cPkl(model_path)
    assert 'species' not in model_state
    model_state['species'] = species
    save_model(model_state, model_path)
    return model_path


@register_ibs_method
def aoi_train(ibs, species_list=None):
    from ibeis_cnn.ingest_ibeis import get_aoi_training_data
    from ibeis_cnn.process import numpy_processed_directory4
    from ibeis_cnn.models.aoi import train_aoi
    from ibeis_cnn.utils import save_model
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_aoi_training_data(ibs, data_path, target_species_list=species_list)
    id_file, X_file, y_file = numpy_processed_directory4(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'aoi')
    model_path = train_aoi(output_path, X_file, y_file)
    model_state = ut.load_cPkl(model_path)
    assert 'species_list' not in model_state
    model_state['species_list'] = species_list
    save_model(model_state, model_path)
    return model_path


@register_ibs_method
def aoi2_train(ibs, species_list=None, train_gid_list=None, purge=True, cache=False):
    from ibeis_cnn.ingest_ibeis import get_aoi2_training_data
    from ibeis_cnn.process import numpy_processed_directory5
    from ibeis_cnn.models.aoi2 import train_aoi2
    from ibeis_cnn.utils import save_model
    data_path = join(ibs.get_cachedir(), 'extracted')
    extracted_path = get_aoi2_training_data(ibs, dest_path=data_path,
                                            target_species_list=species_list,
                                            train_gid_list=train_gid_list,
                                            purge=purge,
                                            cache=cache)
    id_file, X_file, y_file = numpy_processed_directory5(extracted_path)
    output_path = join(ibs.get_cachedir(), 'training', 'aoi2')
    model_path = train_aoi2(output_path, X_file, y_file)
    model_state = ut.load_cPkl(model_path)
    assert 'species_list' not in model_state
    model_state['species_list'] = species_list
    save_model(model_state, model_path)
    return model_path


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.other.detecttrain
        python -m ibeis.other.detecttrain --allexamples
        python -m ibeis.other.detecttrain --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    ut.doctest_funcs()
