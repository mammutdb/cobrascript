# -*- coding: utf-8 -*-

x = jQuery(".item")
x.on("click", lambda e: e.preventDefault())


def fooController(scope, rootScope, config):
    def updateIssue():
        pass

    def updateUserStory():
        pass

    scope.updateIssue = updateIssue
    scope.updateUserStory = updateUserStory


fooController["$inject"] = ["$scope", "$rootScope", "config"]
tttt = xxx = 222
