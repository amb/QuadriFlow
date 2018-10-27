#include "config.hpp"
#include "field-math.hpp"
#include "loader.hpp"
#include "optimizer.hpp"
#include "parametrizer.hpp"

#include <pybind11/eigen.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <omp.h>

namespace py = pybind11;

std::tuple<std::vector<Eigen::Vector3d>, std::vector<Eigen::Vector4i>> remesh(
    MatrixXd positions, MatrixXi indices, int polycount, bool psharp, bool ascale) {
    Parametrizer field;

	// openmp debugging
#ifdef WITH_OMP
    printf("With OpenMP\n");
 //   omp_set_dynamic(0);
	//omp_set_num_threads(16);

 //   int nb_threads = omp_get_max_threads();
 //   printf(">> omp_get_max_thread():\n>> %i\n", nb_threads);

	//#pragma omp parallel
 //   {
 //       std::cout << ">> threads: " << omp_get_num_threads() << std::endl;
 //   }
	//nb_threads = omp_get_num_threads();
 //   printf(">> omp_get_num_threads():\n>> %i\n", nb_threads);

	//int nthreads, tid;

	///* Fork a team of threads giving them their own copies of variables */
	//#pragma omp parallel private(nthreads, tid)
 //   {
 //       /* Obtain thread number */
 //       tid = omp_get_thread_num();
 //       printf("Hello World from thread = %d\n", tid);

 //       /* Only master thread does this */
 //       if (tid == 0) {
 //           nthreads = omp_get_num_threads();
 //           printf("Number of threads = %d\n", nthreads);
 //       }

 //   } /* All threads join master thread and disband */
#endif

#ifdef WITH_TBB
    printf("With TBB\n");
#endif


    setbuf(stdout, NULL);

    int faces = polycount;

    field.F.resize(indices.rows(), indices.cols());
    field.F = indices;

    field.V.resize(positions.rows(), positions.cols());
    field.V = positions;

    //        field.flag_preserve_sharp = 1;
    //        field.flag_adaptive_scale = 1;
    //        field.flag_minimum_cost_flow = 1;
    //        field.flag_aggresive_sat = 1;

    if (psharp) field.flag_preserve_sharp = 1;
    if (ascale) field.flag_adaptive_scale = 1;

    // Initialize
    printf("initialize\n");
    field.Initialize(faces);

    // Solve Orientation Field
    printf("solve orientation field\n");
    Optimizer::optimize_orientations(field.hierarchy);
    field.ComputeOrientationSingularities();

    if (field.flag_adaptive_scale == 1) {
        field.EstimateSlope();
    }
    // Solve for scale
    printf("solve for scale\n");
    Optimizer::optimize_scale(field.hierarchy, field.rho, field.flag_adaptive_scale);
    field.flag_adaptive_scale = 1;

    // Solve for position field
    printf("solve for position field\n");
    Optimizer::optimize_positions(field.hierarchy, field.flag_adaptive_scale);

    field.ComputePositionSingularities();

    // Solve index map
    printf("solve index map\n");
    field.ComputeIndexMap();

    //	field.LoopFace(2);

    printf("Finished Quadriflow.\n");

    return {field.O_compact, field.F_compact};
}

PYBIND11_MODULE(qf_module, m) {
    m.doc() = "Quadriflow Python plugin";

    m.def("remesh", &remesh, "Quadriflow remeshing function");
}