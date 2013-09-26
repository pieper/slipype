"""
export ITK_AUTOLOAD_PATH=/data/acil/pieper/Slicer-superbuild/Slicer-build/lib/Slicer-4.2/ITKFactories
export PATH=${PATH}:/data/acil/pieper/Slicer-superbuild/Slicer-build/lib/Slicer-4.2/cli-modules
cd /data/acil/pieper/nipype/babybrains

execfile('/data/acil/pieper/nipype/babybrains/babybrains.py')
"""

# debug mode
from nipype import config
#config.enable_debug_mode()


# system
import os                                    # system functions

# nipype general 
import nipype.interfaces.utility as niu      # util
import nipype.interfaces.io as nio           # Data i/o
import nipype.pipeline.engine as pe          # pypeline engine


# slicer nipype
from nipype.interfaces.slicer.filtering import n4itkbiasfieldcorrection as n4
from nipype.interfaces.slicer import HistogramMatching as hm
from nipype.interfaces.slicer.registration.brainsfit import BRAINSFit as bf

#
## The pipeline - files to n4 to hm to brainsfit output
#

# first, the normalization pipelet

# bias correction
n4Node = pe.Node(interface=n4.N4ITKBiasFieldCorrection(), name='n4Node')
n4Node.inputs.outputImageName = True

# histogram matching
hmNode = pe.Node(interface=hm(), name='hmNode')
hmNode.inputs.referenceVolume = os.path.join(os.path.abspath('../../data/babybrains'), 'orig/mprage-19.mgz')
hmNode.inputs.outputVolume = True

# registration to subject
bfNode = pe.Node(interface=bf(), name='bfNode')
bfNode.inputs.fixedVolume = os.path.join(os.path.abspath('../../data/babybrains'), 'orig/mprage-19.mgz')
bfNode.inputs.useRigid = True
bfNode.inputs.useAffine = True
bfNode.inputs.outputVolume = True

# connect the normalization pipelet
normalization = pe.Workflow(name='normalization')
normalization.connect(n4Node, 'outputImageName', hmNode, 'inputVolume')
normalization.connect(hmNode, 'outputVolume', bfNode, 'movingVolume')


# what data to run

infosource = pe.Node(niu.IdentityInterface(fields=['subject_id',]), name='infosource')
infosource.iterables = ('subject_id', range(3,41))
#infosource.iterables = ('subject_id', range(3,4))


# the file grabbing pipelet
datasource = pe.Node(interface=nio.DataGrabber(
					infields=['subject_id'], 
					outfields=['original_scan']), 
					name = 'datasource')
datasource.inputs.base_directory = os.path.abspath('../../data/babybrains')
datasource.inputs.template = 'orig/mprage-%d.mgz'
datasource.inputs.sort_filelist = False


# the data storing pipelet
datasink = pe.Node(interface=nio.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.abspath('output')


# the babybrains pipeline
babybrains = pe.Workflow(name='babybrains')
babybrains.base_dir = '/data/acil/pieper/tmp'

babybrains.connect(infosource, 'subject_id', datasource, 'subject_id')
babybrains.connect(datasource, 'original_scan', normalization, 'n4Node.inputImageName')
babybrains.connect(normalization, 'bfNode.outputVolume', datasink, 'normalized')
toString = lambda x: str(x)
babybrains.connect(infosource, ('subject_id',toString), datasink, 'container')

babybrains.config['execution'].update(**{'local_hash_check': True})
#babybrains.run()
babybrains.run(plugin='LSF', plugin_args={'bsub_args': '-q short'})
#babybrains.write_graph(graph2use='flat')
