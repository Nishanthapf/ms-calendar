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

		shim.get_distribution = get_distribution
		shim.DistributionNotFound = Exception
		shim.require = lambda *args, **kwargs: None
		sys.modules["pkg_resources"] = shim
