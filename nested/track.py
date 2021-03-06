import random
import os
import csv


class QueryParamSource:
    # We need to stick to the param source API
    # noinspection PyUnusedLocal
    def __init__(self, track, params, **kwargs):
        self._params = params
        # here we read the queries data file into arrays which we'll then later use randomly.
        self.tags = []
        self.dates = []
        # be predictably random. The seed has been chosen by a fair dice roll. ;)
        random.seed(4)
        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.csv"), "r") as ins:
            csvreader = csv.reader(ins)
            for row in csvreader:
                self.tags.append(row[0])
                self.dates.append(row[1])

    # We need to stick to the param source API
    # noinspection PyUnusedLocal
    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1


class SortedTermQueryParamSource(QueryParamSource):
    def params(self):
        result = {
            "body": {
                "query": {
                    "match": {
                        "tag": "%s" % random.choice(self.tags)
                    }
                },
                "sort": [
                    {
                        "answers.date": {
                            "mode": "max",
                            "order": "desc",
                            "nested_path": "answers"
                        }
                    }
                ]
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result


class TermQueryParamSource(QueryParamSource):
    def params(self):
        result = {
            "body": {
                "query": {
                    "match": {
                        "tag": "%s" % random.choice(self.tags)
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result


class NestedQueryParamSource(QueryParamSource):
    def params(self):
        result = {
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "tag": "%s" % random.choice(self.tags)
                                }
                            },
                            {
                                "nested": {
                                    "path": "answers",
                                    "query": {
                                        "range": {
                                            "answers.date": {
                                                "lte": "%s" % random.choice(self.dates)
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result


class NestedQueryParamSourceWithInnerHits(QueryParamSource):
    def params(self):
        result = {
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "tag": "%s" % random.choice(self.tags)
                                }
                            },
                            {
                                "nested": {
                                    "path": "answers",
                                    "query": {
                                        "range": {
                                            "answers.date": {
                                                "lte": "%s" % random.choice(self.dates)
                                            }
                                        }
                                    },
                                    "inner_hits": {
                                        "size": self._params["inner_hits_size"]
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": self._params["size"]
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result


def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))


def register(registry):
    try:
        major, minor, patch, _ = registry.meta_data["rally_version"]
    except AttributeError:
        # We must be below Rally 0.8.2 (did not provide version metadata).
        # register "refresh" for older versions of Rally. Newer versions have support out of the box.
        registry.register_runner("refresh", refresh)

    registry.register_param_source("nested-query-source", NestedQueryParamSource)
    registry.register_param_source("nested-query-source-with-inner-hits", NestedQueryParamSourceWithInnerHits)
    registry.register_param_source("term-query-source", TermQueryParamSource)
    registry.register_param_source("sorted-term-query-source", SortedTermQueryParamSource)
