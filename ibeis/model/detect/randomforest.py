# """
# Interface to pyrf random forest object detection.
# """
# from __future__ import absolute_import, division, print_function
# from os.path import exists, join
# # from six.moves import zip, map, range
# from ibeis.model.detect import grabmodels
# # from vtool import image as gtool
# from detecttools.directory import Directory
# import utool as ut
# import vtool as vt
# import cv2
# import pyrf
# # import multiprocessing
# import random
# (print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[randomforest]')


# VERBOSE_RF = ut.get_argflag('--verbrf') or ut.VERBOSE


# def train(ibs, gid_list, trees_path=None, species=None, **kwargs):
#     # Ensure directories for negatives
#     if trees_path is None:
#         trees_path = join(ibs.get_ibsdir(), 'trees')
#     negatives_cache = join(ibs.get_cachedir(), 'pyrf_train_negatives')
#     if exists(negatives_cache):
#         ut.remove_dirs(negatives_cache)
#     ut.ensuredir(negatives_cache)

#     # Get positive chip paths
#     if species is None:
#         aids_list = ibs.get_image_aids(gid_list)
#     else:
#         aids_list = ibs.get_image_aids_of_species(gid_list, species)
#     aid_list = ut.flatten(aids_list)
#     train_pos_cpath_list = ibs.get_annot_chip_fpaths(aid_list)

#     # Get negative chip paths
#     train_neg_cpath_list = []
#     while len(train_neg_cpath_list) < len(train_pos_cpath_list):
#         sample = random.randint(0, len(gid_list) - 1)
#         gid = gid_list[sample]
#         img_width, img_height = ibs.get_image_sizes(gid)
#         size = min(img_width, img_height)
#         if species is None:
#             aid_list = ibs.get_image_aids(gid)
#         else:
#             aid_list = ibs.get_image_aids(gid, species)
#         annot_bbox_list = ibs.get_annot_bboxes(aid_list)
#         # Find square patches
#         square = random.randint(int(size / 4), int(size / 2))
#         xmin = random.randint(0, img_width - square)
#         xmax = xmin + square
#         ymin = random.randint(0, img_height - square)
#         ymax = ymin + square
#         if _valid_candidate((xmin, xmax, ymin, ymax), annot_bbox_list):
#             print("CREATING", xmin, xmax, ymin, ymax)
#             img = ibs.get_images(gid)
#             img_path = join(negatives_cache, "neg_%07d.JPEG" % (len(train_neg_cpath_list), ))
#             img = img[ymin:ymax, xmin:xmax]
#             cv2.imwrite(img_path, img)
#             train_neg_cpath_list.append(img_path)

#     # Train trees
#     detector = pyrf.Random_Forest_Detector()
#     detector.train(train_pos_cpath_list, train_neg_cpath_list, trees_path, **kwargs)
#     # Remove cached negatives directory
#     ut.remove_dirs(negatives_cache)


# def detect_gid_list_with_species(ibs, gid_list, species, downsample=True, **kwargs):
#     tree_path_list = _get_models(species)
#     return detect_gid_list(ibs, gid_list, tree_path_list, downsample=downsample, **kwargs)


# def detect_gid_list(ibs, gid_list, tree_path_list, downsample=True, **kwargs):
#     if downsample:
#         gpath_list = ibs.get_image_detectpaths(gid_list)
#         neww_list = [vt.open_image_size(gpath)[0] for gpath in gpath_list]
#         oldw_list = [oldw for (oldw, oldh) in ibs.get_image_sizes(gid_list)]
#         downsample_list = [oldw / neww for oldw, neww in zip(oldw_list, neww_list)]
#     else:
#         gpath_list = ibs.get_image_paths(gid_list)
#         downsample_list = [None] * len(gpath_list)
#     # Run detection
#     results_iter = detect(ibs, gpath_list, downsample_list, tree_path_list, **kwargs)
#     # Upscale the results
#     for downsample, result_list in zip(downsample_list, results_iter):
#         # Upscale the results back up to the original image size
#         if downsample is not None and downsample != 1.0:
#             for result in result_list:
#                 for key in ['centerx', 'centery', 'xtl', 'ytl', 'width', 'height']:
#                     result[key] *= downsample
#         yield result


# def detect(ibs, gpath_list, tree_path_list, **kwargs):
#     # Get scales from detect config, if not specified
#     if 'scale_list' not in kwargs.keys() is None:
#         kwargs['scale_list'] = map(float, ibs.cfg.detect_cfg.scale_list.split(','))
#         assert all([ isinstance(float, scale) for scale in kwargs['scale_list'] ])
#     # Run detection
#     detector = pyrf.Random_Forest_Detector()
#     forest = detector.forest(tree_path_list)
#     results_iter = detector.detect(forest, gpath_list, **kwargs)
#     return results_iter


# ########################


# def _overlap_percentage((xmin1, xmax1, ymin1, ymax1), (xmin2, xmax2, ymin2, ymax2)):
#         width1, height1 = xmax1 - xmin1, ymax1 - ymin1
#         width2, height2 = xmax2 - xmin2, ymax2 - ymin2
#         x_overlap = max(0, min(xmax1, xmax2) - max(xmin1, xmin2))
#         y_overlap = max(0, min(ymax1, ymax2) - max(ymin1, ymin2))
#         area_overlap = float(x_overlap * y_overlap)
#         area_total = min(width1 * height1, width2 * height2)
#         percentage = area_overlap / area_total
#         return percentage


# def _valid_candidate(candidate, annot_bbox_list, overlap=0.0, tries=10):
#     for i in range(tries):
#         valid = True
#         for annot_bbox in annot_bbox_list:
#             xtl, ytl, width, height = annot_bbox
#             xmin, xmax, ymin, ymax = xtl, xtl + width, ytl, ytl + height
#             if _overlap_percentage(candidate, (xmin, xmax, ymin, ymax)) > overlap:
#                 valid = False
#                 break  # break inner loop
#         if valid:
#             return True
#     return False


# def _get_models(species, modeldir='default', verbose=VERBOSE_RF):
#     # Ensure all models downloaded and accounted for
#     grabmodels.ensure_models(modeldir=modeldir, verbose=verbose)
#     trees_path = grabmodels.get_species_trees_paths(species, modeldir=modeldir)
#     if ut.checkpath(trees_path, verbose=verbose):
#         direct = Directory(trees_path, include_extensions=['txt'])
#         print(direct.files())
#         return direct.files()
#     else:
#         # If the models do not exist, return None
#         return None


"""
Interface to pyrf random forest object detection.
"""
from __future__ import absolute_import, division, print_function
from os.path import splitext, exists
from six.moves import zip, map, range
from ibeis.model.detect import grabmodels
from vtool import image as gtool
import utool as ut
import pyrf
import multiprocessing
(print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[randomforest]')


"""
from ibeis.model.detect import randomforest
dir(randomforest)
func = randomforest.ibeis_generate_image_detections
print(ut.make_default_docstr(func))
"""


VERBOSE_RF = ut.get_argflag('--verbrf') or ut.VERBOSE


#=================
# IBEIS INTERFACE
#=================


def ibeis_generate_image_detections(ibs, gid_list, species, verbose=VERBOSE_RF, **detectkw):
    """
    detectkw can be: save_detection_images, save_scales, draw_supressed,
    detection_width, detection_height, percentage_left, percentage_top,
    nms_margin_percentage

    Args:
        ibs (IBEISController):
        gid_list (list):
        species (?):

    Yeilds:
        tuple: tuples of image ids and bounding boxes
    """
    if verbose:
        print('[randomforest] +--- BEGIN ibeis_generate_image_detections')
        print('[randomforest] * species = %r' % (species,))
        print('[randomforest] * len(gid_list) = %r' % (len(gid_list),))
    #
    # Resize to a standard image size prior to detection
    src_gpath_list = list(map(str, ibs.get_image_detectpaths(gid_list)))
    dst_gpath_list = [splitext(gpath)[0] + '_result' for gpath in src_gpath_list]

    # Close any open processes
    ut.close_pool()

    # Get sizes of the original and resized images for final scale correction
    neww_list = [gtool.open_image_size(gpath)[0] for gpath in src_gpath_list]
    oldw_list = [oldw for (oldw, oldh) in ibs.get_image_sizes(gid_list)]
    scale_list = [oldw / neww for oldw, neww in zip(oldw_list, neww_list)]

    # Detect on scaled images
    #ibs.cfg.other_cfg.ensure_attr('detect_use_chunks', True)
    use_chunks = ibs.cfg.other_cfg.detect_use_chunks
    modeldir   = ibs.get_detect_modeldir()

    generator = detect_species_bboxes(src_gpath_list, dst_gpath_list, species,
                                      use_chunks=use_chunks, modeldir=modeldir,
                                      **detectkw)

    for gid, scale, detect_tup in zip(gid_list, scale_list, generator):
        (bboxes, confidences, img_conf) = detect_tup
        # Unscale results
        unscaled_bboxes = [_scale_bbox(bbox_, scale) for bbox_ in bboxes]
        for index in range(len(unscaled_bboxes)):
            bbox = unscaled_bboxes[index]
            confidence = float(confidences[index])
            yield gid, bbox, confidence, img_conf
    if verbose:
        print('[randomforest] L___ FINISH ibeis_generate_image_detections')


def compute_hough_images(src_gpath_list, dst_gpath_list, species,
                         use_chunks=True, quick=True, verbose=VERBOSE_RF,
                         modeldir='default'):
    """
    Args:
        src_gpath_list (list):
        dst_gpath_list (list):
        species (?):
        quick (bool):

    Returns:
        None

        import utool; utool.print_auto_docstr('ibeis.model.detect.randomforest', 'compute_hough_images')
    """
    # Define detect dict
    detectkw = {
        'quick': quick,
        'save_detection_images': True,
        'save_scales': False,
    }
    _compute_hough(src_gpath_list, dst_gpath_list, species,
                   use_chunks=use_chunks, modeldir=modeldir, **detectkw)


# TODO use this function so modeldir can just be dependant on an
# ibs or qreq_ object
#def computed_ibeis_probability_images(src_gpath_list, dst_gpath_list, species):


def compute_probability_images(src_gpath_list, dst_gpath_list, species,
                               use_chunks=True, quick=False, modeldir='default',
                               verbose=VERBOSE_RF):
    """
    Args:
        src_gpath_list (list):
        dst_gpath_list (list):
        species (?):
        quick (bool):

    Returns:
        None

    import utool; utool.print_auto_docstr('ibeis.model.detect.randomforest', 'compute_hough_images')

    """
    # Define detect dict
    detectkw = {
        'single': True,  # single is True = probability, False is hough
        'quick': quick,
        'save_detection_images': True,
        'save_scales': False,
    }
    _compute_hough(src_gpath_list, dst_gpath_list, species, modeldir=modeldir,
                   verbose=verbose, **detectkw)


def _compute_hough(src_gpath_list, dst_gpath_list, species, use_chunks=True,
                    modeldir='default', verbose=VERBOSE_RF, **detectkw):
    """
    FIXME. This name is not accurate
    """
    assert len(src_gpath_list) == len(dst_gpath_list)

    # FIXME: images are not invalidated so this cache doesnt always work
    isvalid_list = [exists(gpath + '.png') for gpath in dst_gpath_list]
    dirty_src_gpaths = ut.get_dirty_items(src_gpath_list, isvalid_list)
    dirty_dst_gpaths = ut.get_dirty_items(dst_gpath_list, isvalid_list)
    num_dirty = len(dirty_src_gpaths)
    if num_dirty > 0:
        if verbose:
            print('[detect.rf] making hough images for %d images' % num_dirty)
        generator = detect_species_bboxes(dirty_src_gpaths, dirty_dst_gpaths,
                                          species, use_chunks=use_chunks,
                                          modeldir=modeldir, verbose=verbose,
                                          **detectkw)
        # Execute generator
        for tup in generator:
            # FIXME: pyrf does not respect destintation image paths
            pass


#=================
# HELPER FUNCTIONS
#=================


def _scale_bbox(bbox, s):
    """
    helper function

    Args:
        bbox (tuple): bounding box
        s (float): scale factor

    Returns:
        bbox2
    """
    bbox_scaled = (s * _ for _ in bbox)
    bbox_round = list(map(round, bbox_scaled))
    bbox_int   = list(map(int,   bbox_round))
    bbox2      = tuple(bbox_int)
    return bbox2


def _get_detector(species, quick=True, single=False, modeldir='default',
                  verbose=VERBOSE_RF):
    """
    Args:
        species (str): species key
        quick (bool):
        single (bool):
        modeldir (str): directory where models will be

    Returns:
        tuple: (detector, forest)

    Example1:
        >>> # SLOW_DOCTEST
        >>> # Test existing model
        >>> from ibeis.model.detect.randomforest import *  # NOQA
        >>> from ibeis.model.detect import randomforest
        >>> species = 'zebra_plains'
        >>> quick = True
        >>> single = False
        >>> modeldir = 'default'
        >>> (detector, forest) = randomforest._get_detector(species, quick, single, modeldir)
        >>> result = str(list(map(type, (detector, forest))))
        >>> print(result)
        [<class 'pyrf._pyrf.Random_Forest_Detector'>, <type 'int'>]

    Example2:
        >>> # ENABLE_DOCTEST
        >>> # Test non-existing model
        >>> from ibeis.model.detect.randomforest import *  # NOQA
        >>> from ibeis.model.detect import randomforest
        >>> species = 'dropbear'
        >>> quick = True
        >>> single = False
        >>> modeldir = 'default'
        >>> (detector, forest) = randomforest._get_detector(species, quick, single, modeldir)
        >>> result = str(list(map(type, (detector, forest))))
        >>> print(result)
        [<type 'NoneType'>, <type 'NoneType'>]

    """
    # Ensure all models downloaded and accounted for
    grabmodels.ensure_models(modeldir=modeldir, verbose=verbose)
    # Create detector
    if single:
        if quick:
            print("[detect.rf] Running quick (single scale) probability image")
            config = {
                'scales': '1 1.0',
                'out_scale': 255,
                'pos_like': 1,
            }
        else:
            config = {
                'out_scale': 255,
                'pos_like': 1,
            }
    else:
        if quick:
            config = {}
        else:
            config = {
                'scales': '11 2.0 1.75 1.5 1.33 1.15 1.0 0.75 0.55 0.40 0.30 0.20',
            }
    if verbose:
        print('[randomforest] building detector')
    trees_path = grabmodels.get_species_trees_paths(species, modeldir=modeldir)
    if ut.checkpath(trees_path, verbose=verbose):
        # Load forest, so we don't have to reload every time
        if verbose:
            print('[randomforest] loading forest')
        detector = pyrf.Random_Forest_Detector(verbose=verbose, rebuild=False, **config)
        forest = detector.load(trees_path, species + '-', num_trees=25)
        # TODO: WE NEED A WAY OF ASKING IF THE LOAD WAS SUCCESSFUL
        # SO WE CAN HANDLE IT GRACEFULLY FROM PYTHON
        return detector, forest
    else:
        # If the models do not exist return None
        return None, None


def _get_detect_config(**detectkw):
    detect_config = {
        'percentage_top':    0.40,
    }
    detect_config.update(detectkw)
    return detect_config


#=================
# PYRF INTERFACE
#=================


def format_pyrf_results(results):
    bboxes = [(minx, miny, (maxx - minx), (maxy - miny))
              for (centx, centy, minx, miny, maxx, maxy, confidence, supressed)
              in results if supressed == 0]

    #x_arr = results[:, 2]
    #y_arr = results[:, 3]
    #w_arr = results[:, 4] - results[:, 2]
    #h_arr = results[:, 5] - results[:, 3]
    #bboxes = np.hstack((x_arr, y_arr, w_arr, h_arr))
    # Unpack unsupressed bounding boxes

    confidences = [confidence
                   for (centx, centy, minx, miny, maxx, maxy, confidence, supressed)
                   in results if supressed == 0]

    if len(results) > 0:
        image_confidence = max([float(result[6]) for result in results])
    else:
        image_confidence = 0.0
    return bboxes, confidences, image_confidence


def detect_species_bboxes(src_gpath_list, dst_gpath_list, species, quick=True,
                          single=False, use_chunks=False, modeldir='default',
                          verbose=VERBOSE_RF, **detectkw):
    """
    Generates bounding boxes for each source image
    For each image yeilds a list of bounding boxes

    Args:
        src_gpath_list (list):
        dst_gpath_list (list):
        species        (str):
        quick          (bool):
        single         (bool):
        use_chunks     (bool):
        modeldir       (str):
        verbose        (bool):

    CommandLine:
        python -m ibeis.model.detect.randomforest --test-detect_species_bboxes

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.model.detect.randomforest import *  # NOQA
        >>> src_gpath_list = '?'
        >>> dst_gpath_list = '?'
        >>> species = '?'
        >>> quick = True
        >>> single = False
        >>> use_chunks = False
        >>> modeldir = 'default'
        >>> verbose = False
        >>> result = detect_species_bboxes(src_gpath_list, dst_gpath_list, species, quick, single, use_chunks, modeldir, verbose)
        >>> print(result)
    """
    nImgs = len(src_gpath_list)
    if verbose:
        print('[detect.rf] Begining %s detection' % (species,))
    detect_lbl = 'detect %s: ' % species
    #mark_prog, end_prog = ut.progress_func(nImgs, detect_lbl, flush_after=1)

    detect_config = _get_detect_config(**detectkw)
    detector, forest = _get_detector(species, quick=quick, single=single,
                                     modeldir=modeldir, verbose=verbose)
    if detector is None:
        raise StopIteration('species=%s does not have models trained' % (species,))
    detector.set_detect_params(**detect_config)

    chunksize = min(8, multiprocessing.cpu_count())
    use_chunks_ = use_chunks and nImgs >= chunksize

    if verbose:
        print('[rf] src_gpath_list = ' + ut.truncate_str(ut.list_str(src_gpath_list)))
        print('[rf] dst_gpath_list = ' + ut.truncate_str(ut.list_str(dst_gpath_list)))
    if use_chunks_:
        #if verbose:
        print('[rf] detect in chunks. chunksize=%d' % (chunksize,))
        pathtup_iter = list(zip(src_gpath_list, dst_gpath_list))
        chunk_iter = ut.ichunks(pathtup_iter, chunksize)
        nTotal = ut.iceil(nImgs / chunksize)
        chunk_progiter = ut.ProgressIter(chunk_iter, lbl=detect_lbl,
                                         nTotal=nTotal, freq=1)
        for ic, chunk in enumerate(chunk_progiter):
            src_gpath_list = [tup[0] for tup in chunk]
            dst_gpath_list = [tup[1] for tup in chunk]
            #mark_prog(ic * chunksize)
            results_list = detector.detect_many(forest, src_gpath_list, dst_gpath_list, use_openmp=True)

            for results in results_list:
                bboxes, confidences, image_confidence =  format_pyrf_results(results)
                yield bboxes, confidences, image_confidence
    else:
        if verbose:
            print('[rf] detect one image at a time')
        pathtup_iter = zip(src_gpath_list, dst_gpath_list)
        pathtup_progiter = ut.ProgressIter(pathtup_iter, lbl=detect_lbl,
                                           nTotal=nImgs, freq=1)
        for ix, (src_gpath, dst_gpath) in enumerate(pathtup_progiter):
            #mark_prog(ix)
            results = detector.detect(forest, src_gpath, dst_gpath)
            bboxes, confidences, image_confidence =  format_pyrf_results(results)
            yield bboxes, confidences, image_confidence
    #end_prog()


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.model.detect.randomforest
        python -m ibeis.model.detect.randomforest --allexamples
        python -m ibeis.model.detect.randomforest --allexamples --noface --nosrc
    """
    multiprocessing.freeze_support()  # for win32
    ut.doctest_funcs()
