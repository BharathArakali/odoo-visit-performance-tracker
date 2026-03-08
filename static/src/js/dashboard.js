/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

class VisitDashboard extends Component {
    static template = "visit_performance_tracker.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            totalVisits: 0,
            totalDone: 0,
            totalMissed: 0,
            totalDraft: 0,
            avgProductivity: 0,
            salesmanStats: [],
            stateStats: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        // Fetch all visit plans
        const visits = await this.orm.searchRead(
            "visit.plan",
            [],
            ["state", "productivity_score", "salesman_id"]
        );

        // KPI calculations
        this.state.totalVisits = visits.length;
        this.state.totalDone = visits.filter(v => v.state === "done").length;
        this.state.totalMissed = visits.filter(v => v.state === "missed").length;
        this.state.totalDraft = visits.filter(v => v.state === "draft").length;

        const totalProductivity = visits.reduce((sum, v) => sum + v.productivity_score, 0);
        this.state.avgProductivity = visits.length
            ? (totalProductivity / visits.length).toFixed(1)
            : 0;

        // State stats for bar chart
        this.state.stateStats = [
            { label: "Done", count: this.state.totalDone, color: "#28a745" },
            { label: "Missed", count: this.state.totalMissed, color: "#dc3545" },
            { label: "Draft", count: this.state.totalDraft, color: "#6c757d" },
        ];

        // Productivity per salesman
        const salesmanMap = {};
        for (const v of visits) {
            if (v.salesman_id) {
                const name = v.salesman_id[1];
                if (!salesmanMap[name]) {
                    salesmanMap[name] = { total: 0, count: 0 };
                }
                salesmanMap[name].total += v.productivity_score;
                salesmanMap[name].count += 1;
            }
        }
        this.state.salesmanStats = Object.entries(salesmanMap).map(([name, data]) => ({
            name,
            avg: (data.total / data.count).toFixed(1),
        })).sort((a, b) => b.avg - a.avg);
    }

    // Click KPI cards to navigate to filtered list
    viewAll() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "All Visits",
            res_model: "visit.plan",
            view_mode: "list,form",
            domain: [],
        });
    }

    viewDone() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Done Visits",
            res_model: "visit.plan",
            view_mode: "list,form",
            domain: [["state", "=", "done"]],
        });
    }

    viewMissed() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Missed Visits",
            res_model: "visit.plan",
            view_mode: "list,form",
            domain: [["state", "=", "missed"]],
        });
    }

    viewDraft() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Draft Visits",
            res_model: "visit.plan",
            view_mode: "list,form",
            domain: [["state", "=", "draft"]],
        });
    }

    // Bar width for charts
    getBarWidth(value) {
        const max = Math.max(...this.state.stateStats.map(s => s.count), 1);
        return Math.round((value / max) * 100);
    }

    getSalesmanBarWidth(avg) {
        return Math.min(Math.round(avg), 100);
    }
}

registry.category("actions").add("visit_performance_tracker.dashboard", VisitDashboard);