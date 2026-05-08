import sys
import types


def execute():
	try:
		import pkg_resources  # noqa
	except ImportError:
		shim = types.ModuleType("pkg_resources")

		def get_distribution(name):
			try:
				import importlib.metadata

				version = importlib.metadata.version(name)
				return types.SimpleNamespace(version=version)
			except Exception:
				return types.SimpleNamespace(version="0.0.0")

		def resource_filename(package_or_requirement, resource_name):
			import importlib.util
			import os

			try:
				spec = importlib.util.find_spec(package_or_requirement)
				if spec and spec.origin:
					return os.path.join(os.path.dirname(spec.origin), resource_name)
			except Exception:
				pass
			return resource_name

		shim.get_distribution = get_distribution
		shim.resource_filename = resource_filename
		shim.DistributionNotFound = Exception
		shim.require = lambda *args, **kwargs: None
		sys.modules["pkg_resources"] = shim
