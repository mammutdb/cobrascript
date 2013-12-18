# -*- coding: utf-8 -*-

import _global as g

def backlog_controller(scope, root_scope, route_params, rs, data, i18next):
    root_scope.page_title = i18next.t("common.baclog")
    root_scope.page_section = "backlog"
    root_scope.page_breadcrumbs = [["", ""],[i18next.t("common.backlog"), None]]
    root_scope.project_id = parseInt(root_scope.pid, 10)

    scope.stats = {}

    def on_project_stats_loaded():
        if scope.project_stats.total_points > 0:
            scope.percentage_closed_points = ((scope.project_stats.closed_points * 100) /
                                              scope.project_stats.total_points)
        else:
            scope.percentage_closed_points = 0

    def on_milestone_loaded(ctx, _data):
        if _data.length > 0:
            root_scope.sprint_id = _data[0].id

    on_fn = scope["$on"]
    emit_fn = scope["$emit"]

    on_fn("stats:update", lambda: data.load_project_stats(scope).then(on_project_stats_loaded))
    on_fn("milestones:loaded", lambda: on_project_stats_loaded())

    def on_project_load():
        emit_fn("stats:update")
        data.loade_users_and_roles(scope)

    promise = data.load_project(scope)
    promise.then(on_project_load)

    class MyObject:
        def sample_method():
            return 2
