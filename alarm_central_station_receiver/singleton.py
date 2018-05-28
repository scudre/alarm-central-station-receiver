"""
Copyright (2018) Chris Scuderi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


class Singleton(object):
    """
    Helper decorator class for creating single instances of a class
    """

    def __init__(self, klass):
        self._klass = klass
        self._instance = None

    def __call__(self):
        if not self._instance:
            self._instance = self._klass()

        return self._instance

    def __instancecheck__(self, inst):
        return isinstance(inst, self._klass)
