#include "config.hpp"
#include "field-math.hpp"
#include "loader.hpp"
#include "optimizer.hpp"
#include "parametrizer.hpp"

#include <pybind11/eigen.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

Parametrizer field;

namespace py = pybind11;

std::tuple<std::vector<std::vector<double>>, std::vector<std::vector<int>>> 
remesh(std::vector<std::vector<double>> positions, std::vector<std::vector<int>> indices) {
    setbuf(stdout, NULL);

    int faces = -1;

    field.F.resize(3, indices.size());
    for (int i = 0; i < indices.size(); i++) {
        field.F.col(i)[0] = indices[i][0];
        field.F.col(i)[1] = indices[i][1];
        field.F.col(i)[2] = indices[i][2];
    }

    field.V.resize(3, positions.size());
    for (int i = 0; i < positions.size(); i++) {
        field.V.col(i)[0] = positions[i][0];
        field.V.col(i)[1] = positions[i][1];
        field.V.col(i)[2] = positions[i][2];
    }

    //        field.flag_preserve_sharp = 1;
    //        field.flag_adaptive_scale = 1;
    //        field.flag_minimum_cost_flow = 1;
    //        field.flag_aggresive_sat = 1;

    // Initialize
    field.Initialize(faces);

    // Solve Orientation Field
    Optimizer::optimize_orientations(field.hierarchy);
    field.ComputeOrientationSingularities();

    if (field.flag_adaptive_scale == 1) {
        field.EstimateSlope();
    }
    // Solve for scale
    Optimizer::optimize_scale(field.hierarchy, field.rho, field.flag_adaptive_scale);
    field.flag_adaptive_scale = 1;

    // Solve for position field
    Optimizer::optimize_positions(field.hierarchy, field.flag_adaptive_scale);

    field.ComputePositionSingularities();

    // Solve index map
    field.ComputeIndexMap();

    //	field.LoopFace(2);
    std::vector<std::vector<double>> v_out = std::vector<std::vector<double>>();
    std::vector<std::vector<int>> f_out = std::vector<std::vector<int>>();

    for (int i = 0; i < field.O_compact.size(); i++) {
        std::vector<double> v = std::vector<double>();
        v_out.push_back(v);
        v_out[i][0] = field.O_compact[i][0];
        v_out[i][1] = field.O_compact[i][1];
        v_out[i][2] = field.O_compact[i][2];
    }

    for (int i = 0; i < field.F_compact.size(); i++) {
        std::vector<int> f = std::vector<int>();
        f_out.push_back(f);
        f_out[i][0] = field.F_compact[i][0];
        f_out[i][1] = field.F_compact[i][1];
        f_out[i][2] = field.F_compact[i][2];
    }

    return {v_out, f_out};
}

PYBIND11_MODULE(qf_module, m) {
    m.doc() = "Quadriflow Python plugin";

    m.def("remesh", &remesh, "Quadriflow remeshing function");
}