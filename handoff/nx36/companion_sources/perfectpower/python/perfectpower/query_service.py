"""Versioned JSONL service: one isolated response per request, no code eval."""
import argparse
import json
import sys
from .catalogue import Catalogue, encoded
from .divisor_square import WorkLimit

METHODS = dict(
    completion_planner={'summary','evidence','count','completions','select','rank','optimize','page','sample'},
    rational_series={'summary','evidence','coefficient','terms'},
    theta_series={'summary','evidence','coefficient','terms'},
    budget_population={'summary','evidence','count','cumulative_count','select','rank','page'},
    elliptic_curve={'summary','evidence','point_add','point_multiply','rational_halves','rational_thirds','rational_division','subgroup_preimage','bounded_saturation','subgroup_presentation','saturation_presentation','model_transport','two_isogeny','independence','mordell_two_descent','native_two_torsion','native_halves'},
    differential_module={'summary','evidence','dual','tensor','hom','power','pullback','gauge','horizontal_sections','horizontal_endomorphisms','involution_descent','observable'},
    superelliptic_family={'summary','evidence','observable'},
    binomial_sum={'summary','evidence','term','terms','telescoper','elliptic_bridge'},
    differential_extension={'summary','evidence','element_data','fixed_algebra','hilbert90'},
    symmetry_curve={'summary','evidence','projectors','quotient','observable','involution_decomposition'},
    multi_curve_family={'summary','evidence','specialize','deformation','projective_deformation','root_motion','observable'},
    elliptic_quotient={'summary','evidence','specialize','observable','collisions','root_motion','period_path','point_image','rational_lifts'},
    curve_family={'summary','evidence','specialize','observable','deformation','projective_deformation','root_motion','collisions','local_analysis','frobenius_jet','algebraic_local_chart','algebraic_degenerations','resonant_frobenius','node_branches','ramified_scaling_chart','cyclic_projector_obstruction','de_rham_pairing','horizontal_projectors','check_projector','parameter_domain','parameter_population','integer_points','marked_period','transport','period_path'},
    calibration_policy={'summary','evidence','decide'},diagnostic_policy={'summary','evidence','step','run'},
    projected={'summary','count','select','rank','page','sample','partition','locate','multiplicity','evidence'},
    factorial={'summary','terms','residues'},
    population_comparison={'summary','count','select','locate','classify','transport','page','sample','optimize','evidence'},
    population={'summary', 'count', 'select', 'rank', 'locate', 'page', 'next', 'sample', 'partition', 'optimize', 'evidence'},
    sequence={'summary', 'terms', 'subsequence', 'experiment', 'witness_experiment','diagnostic'}, inverse={'solve', 'solve_box','policy'},
    graph={'event', 'sample'}, geometry={'point', 'segment', 'grid', 'transition', 'transport'},
    combinatorial={'gamma', 'sizes', 'select_size'})


def dispatch(catalogue, request):
    if not isinstance(request, dict) or set(request)-{'request_id', 'op', 'kind', 'specification', 'name', 'replace', 'object', 'method', 'args', 'other', 'predicate'}:
        raise ValueError('unsupported request fields')
    op = request.get('op'); args = request.get('args', {})
    if not isinstance(args, dict):
        raise ValueError('args must be a JSON object')
    if op == 'planning_optimization':
        from .planning import optimize_allocation
        return optimize_allocation(**args)
    if op == 'generating_function':
        from .generating_cli import execute
        return execute(args)
    if op == 'checked_population':
        from .checked_population import population_certificate
        return population_certificate(**args)
    if op == 'checked_global_population':
        from .checked_global_population import global_population_certificate
        return global_population_certificate(**args)
    if op == 'checked_nonlinear_population':
        from .checked_nonlinear_population import nonlinear_population_certificate
        return nonlinear_population_certificate(**args)
    if op == 'checked_pell_population':
        from .checked_pell_population import pell_population_certificate
        return pell_population_certificate(**args)
    if op == 'checked_family_population':
        from .checked_family_population import family_population_certificate
        return family_population_certificate(**args)
    if op == 'checked_pell_family':
        from .checked_pell_family import pell_family_certificate
        return pell_family_certificate(**args)
    if op == 'checked_pell_orbits':
        from .checked_pell_orbits import pell_orbits_certificate
        return pell_orbits_certificate(**args)
    if op == 'checked_auto_population':
        from .automatic_population import automatic_population_certificate
        return automatic_population_certificate(**args)
    if op == 'checked_box':
        from .checked_box import box_certificate
        return box_certificate(**args)
    if op == 'checked_factorial_unit':
        from .checked_factorial_unit import unit_certificate
        return unit_certificate(**args)
    if op == 'checked_landau':
        from .checked_landau import landau_certificate
        return landau_certificate(**args)
    if op in {'semistable_tamagawa','metric_component_group','resonant_frobenius','frobenius_gauge_tail'}:
        from .semistable_tamagawa import rational_root_tamagawa,component_group
        from .resonant_frobenius import normal_form,gauge_tail
        return {'semistable_tamagawa':rational_root_tamagawa,'metric_component_group':component_group,
                'resonant_frobenius':normal_form,'frobenius_gauge_tail':gauge_tail}[op](**args)
    if op == 'register':
        return catalogue.register(request['kind'], request['specification'], request.get('name'), replace=request.get('replace', False))
    if op == 'list':
        return catalogue.list(**args)
    if op == 'definition':
        return catalogue.definition(request['object'])
    if op in {'integer_power_charts', 'verify_integer_power_charts',
              'integer_power_chart_population', 'integer_power_chart_select',
              'integer_power_chart_rank', 'integer_power_chart_scan', 'native_integer_power_charts',
              'branch_integer_power_charts', 'verify_branch_integer_power_charts',
              'scan_branch_integer_power_charts'}:
        from . import integer_valued_power_charts as pc
        result = {'integer_power_charts': pc.power_charts,
                  'verify_integer_power_charts': pc.verify_power_charts,
                  'integer_power_chart_population': pc.chart_population,
                  'integer_power_chart_select': pc.chart_select,
                  'integer_power_chart_rank': pc.chart_rank,
                  'integer_power_chart_scan': pc.chart_scan,
                  'native_integer_power_charts': pc.native_power_charts,
                  'branch_integer_power_charts': pc.branch_power_charts,
                  'verify_branch_integer_power_charts': pc.verify_branch_power_charts,
                  'scan_branch_integer_power_charts': pc.branch_power_scan}[op](**args)
        if op.startswith('verify_'): return dict(valid=result, execution_verified=False)
        if op.startswith('native_'): return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'branching_residue_patch', 'verify_branching_residue_patch',
              'branching_patch_select', 'branching_patch_rank', 'branching_patch_scan',
              'native_branching_residue_patch'}:
        from . import branching_residue_patch as bp
        result = {'branching_residue_patch': bp.branching_patch,
                  'verify_branching_residue_patch': bp.verify_branching_patch,
                  'branching_patch_select': bp.patch_select, 'branching_patch_rank': bp.patch_rank,
                  'branching_patch_scan': bp.patch_scan,
                  'native_branching_residue_patch': bp.native_branching_patch}[op](**args)
        if op.startswith('verify_'): return dict(valid=result, execution_verified=False)
        if op.startswith('native_'): return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'unordered_weighted_determinant', 'verify_unordered_weighted_determinant',
              'native_unordered_weighted_determinant', 'chart_weighted_determinant',
              'verify_chart_weighted_determinant'}:
        from . import unordered_weighted_determinant as wd
        result = {'unordered_weighted_determinant': wd.weighted_determinant,
                  'verify_unordered_weighted_determinant': wd.verify_weighted_determinant,
                  'native_unordered_weighted_determinant': wd.native_weighted_determinant,
                  'chart_weighted_determinant': wd.chart_determinant,
                  'verify_chart_weighted_determinant': wd.verify_chart_determinant}[op](**args)
        if op.startswith('verify_'): return dict(valid=result, execution_verified=False)
        if op.startswith('native_'): return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'rational_power_atlas','verify_rational_power_atlas','rational_power_population',
              'rational_power_select','rational_power_rank','rational_power_scan',
              'rational_power_patch','verify_rational_power_patch','native_rational_power_atlas'}:
        from . import rational_power_atlas as pa
        result={'rational_power_atlas':pa.power_atlas,'verify_rational_power_atlas':pa.verify_power_atlas,
                'rational_power_population':pa.power_population,'rational_power_select':pa.power_select,
                'rational_power_rank':pa.power_rank,'rational_power_scan':pa.power_scan,
                'rational_power_patch':pa.power_patch,'verify_rational_power_patch':pa.verify_power_patch,
                'native_rational_power_atlas':pa.native_power_atlas}[op](**args)
        if op.startswith('verify_'):return dict(valid=result,execution_verified=False)
        if op.startswith('native_'):return dict(lean_source=result,execution_verified=False)
        return result
    if op in {'weighted_gram_determinant','verify_weighted_gram_determinant'}:
        from . import weighted_gram_determinant as uw
        result={'weighted_gram_determinant':uw.weighted_determinant,
                'verify_weighted_gram_determinant':uw.verify_weighted_determinant}[op](**args)
        return dict(valid=result,execution_verified=False) if op.startswith('verify_') else result
    if op in {'weil_spectral', 'weil_operator_spectrum', 'weil_projector_plan'}:
        from . import weil_spectral as ws
        return {'weil_spectral': ws.spectral_packet,
                'weil_operator_spectrum': ws.operator_packet,
                'weil_projector_plan': ws.decomposition_plan}[op](**args)
    if op == 'weil_orbit_certificate':
        from .weil_orbit import exact_orbit_certificate
        return exact_orbit_certificate(**args)
    if op in {'certified_weil_commutant', 'verify_weil_commutant', 'weil_crt_commutant'}:
        from . import weil_commutant as wc
        result = {'certified_weil_commutant': wc.certify_commutant,
                  'verify_weil_commutant': wc.verify_commutant,
                  'weil_crt_commutant': wc.certify_product}[op](**args)
        if op == 'verify_weil_commutant':
            return dict(valid=result, execution_verified=False)
        return result
    if op in {'intersect_residue_atlases', 'verify_residue_atlas_intersection',
              'residue_intersection_population', 'residue_intersection_select',
              'residue_intersection_rank'}:
        from . import residue_atlas_intersection as ri
        result = {'intersect_residue_atlases': ri.intersect_atlases,
                  'verify_residue_atlas_intersection': ri.verify_intersection,
                  'residue_intersection_population': ri.intersection_population,
                  'residue_intersection_select': ri.intersection_select,
                  'residue_intersection_rank': ri.intersection_rank}[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        return result
    if op in {'intersect_residue_atlases_factored', 'verify_residue_atlas_intersection_factored',
              'residue_intersection_factored_contains', 'residue_intersection_factored_population',
              'residue_intersection_factored_select', 'residue_intersection_factored_rank',
              'residue_intersection_factored_scan', 'native_residue_atlas_intersection_factored'}:
        from . import residue_atlas_intersection_factored as ri
        result = {'intersect_residue_atlases_factored': ri.intersect_atlases,
                  'verify_residue_atlas_intersection_factored': ri.verify_intersection,
                  'residue_intersection_factored_contains': ri.intersection_contains,
                  'residue_intersection_factored_population': ri.intersection_population,
                  'residue_intersection_factored_select': ri.intersection_select,
                  'residue_intersection_factored_rank': ri.intersection_rank,
                  'residue_intersection_factored_scan': ri.intersection_scan,
                  'native_residue_atlas_intersection_factored': ri.native_intersection}[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        if op.startswith('native_'):
            return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'residue_atlas_product', 'compose_residue_atlases', 'verify_residue_atlas_product',
              'residue_product_contains', 'residue_product_population', 'residue_product_select',
              'residue_product_rank', 'residue_product_scan', 'native_residue_atlas_product'}:
        from . import residue_atlas_product as rp
        result = {'residue_atlas_product': rp.product_packet, 'compose_residue_atlases': rp.compose_atlases,
                  'verify_residue_atlas_product': rp.verify_product, 'residue_product_contains': rp.product_contains,
                  'residue_product_population': rp.product_population, 'residue_product_select': rp.product_select,
                  'residue_product_rank': rp.product_rank, 'residue_product_scan': rp.product_scan,
                  'native_residue_atlas_product': rp.native_product}[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        if op.startswith('native_'):
            return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'residue_atlas', 'verify_residue_atlas', 'residue_atlas_population',
              'residue_atlas_select', 'residue_atlas_rank', 'residue_atlas_scan', 'native_residue_atlas'}:
        from . import residue_atlas as ra
        functions = {'residue_atlas': ra.atlas_packet, 'verify_residue_atlas': ra.verify_atlas,
                     'residue_atlas_population': ra.atlas_population, 'residue_atlas_select': ra.atlas_select,
                     'residue_atlas_rank': ra.atlas_rank, 'residue_atlas_scan': ra.atlas_scan,
                     'native_residue_atlas': ra.native_atlas}
        result = functions[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        if op.startswith('native_'):
            return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'bounded_residue_patch', 'verify_bounded_residue_patch', 'native_bounded_residue_patch'}:
        from .bounded_residue_patch import patch_packet, verify_patch, native_patch
        result = {'bounded_residue_patch': patch_packet,
                  'verify_bounded_residue_patch': verify_patch,
                  'native_bounded_residue_patch': native_patch}[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        if op.startswith('native_'):
            return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'integral_kernel_packet', 'bounded_auxiliary_packet', 'residue_determinant_packet',
              'verify_integral_kernel', 'verify_bounded_auxiliary', 'verify_residue_determinant',
              'native_integral_kernel', 'native_bounded_auxiliary', 'native_residue_determinant'}:
        from . import residue_determinant as rd
        functions = {'integral_kernel_packet': rd.kernel_packet,
                     'bounded_auxiliary_packet': rd.auxiliary_packet,
                     'residue_determinant_packet': rd.determinant_packet,
                     'verify_integral_kernel': rd.verify_kernel,
                     'verify_bounded_auxiliary': rd.verify_auxiliary,
                     'verify_residue_determinant': rd.verify_determinant,
                     'native_integral_kernel': rd.native_kernel,
                     'native_bounded_auxiliary': rd.native_auxiliary,
                     'native_residue_determinant': rd.native_determinant}
        result = functions[op](**args)
        if op.startswith('verify_'):
            return dict(valid=result, execution_verified=False)
        if op.startswith('native_'):
            return dict(lean_source=result, execution_verified=False)
        return result
    if op in {'verify_elliptic_halves','verify_elliptic_independence'}:
        from .elliptic_certificate_verifier import verify_halves,verify_independence
        checker=verify_halves if op=='verify_elliptic_halves' else verify_independence
        return dict(valid=checker(**args),execution_verified=False)
    if op in {'verify_elliptic_thirds','verify_elliptic_division'}:
        from .elliptic_division_verifier import verify_thirds,verify_division
        checker=verify_thirds if op=='verify_elliptic_thirds' else verify_division
        return dict(valid=checker(**args),execution_verified=False)
    if op in {'integer_valued_polynomial','gamma_integer_arithmetic','native_integer_valued_certificate'}:
        from .integer_valued_polynomial import analyze,gamma_packet,native_certificate
        return {'integer_valued_polynomial':analyze,'gamma_integer_arithmetic':gamma_packet,
                'native_integer_valued_certificate':native_certificate}[op](**args)
    if op in {'repeated_power_free','native_repeated_power_free'}:
        from .fixed_divisor import repeated_power_free,native_repeated_power_free
        return {'repeated_power_free':repeated_power_free,'native_repeated_power_free':native_repeated_power_free}[op](**args)
    if op in {'fixed_divisor','fixed_divisor_admissibility','native_fixed_divisor_certificate'}:
        from .fixed_divisor import fixed_divisor,admissibility,native_certificate
        operations={'fixed_divisor':fixed_divisor,'fixed_divisor_admissibility':admissibility,'native_fixed_divisor_certificate':native_certificate}
        return operations[op](**args)
    if op in {'power_free_local','power_free_wheel','native_power_free_certificate'}:
        from .power_free_local import local_admissibility,power_free_wheel,native_certificate
        operations={'power_free_local':local_admissibility,'power_free_wheel':power_free_wheel,'native_power_free_certificate':native_certificate}
        return operations[op](**args)
    if op == 'native_halves_certificate':
        from .native_halves_certificate import halves_certificate
        return halves_certificate(**args)
    if op == 'native_two_torsion_certificate':
        from .native_rational_certificate import two_torsion_certificate
        return two_torsion_certificate(**args)
    if op == 'native_rational_certificate':
        from .native_rational_certificate import rational_certificate
        return rational_certificate(**args)
    if op == 'native_residue_certificate':
        from .native_residue_certificate import residue_certificate
        return residue_certificate(**args)
    if op == 'native_braid_certificate':
        from .native_braid_certificate import braid_certificate
        return braid_certificate(**args)
    if op=='elliptic_torsion_subgroup_index':
        from .elliptic_torsion_index import torsion_subgroup_index
        return torsion_subgroup_index(**args)
    if op=='verify_elliptic_torsion_subgroup_index':
        from .elliptic_torsion_index import verify_torsion_subgroup_index
        return dict(valid=verify_torsion_subgroup_index(**args),execution_verified=False)
    if op=='pell7_complete':
        from .pell7_complete import certificate
        return certificate()
    if op=='pell7_address':
        from .pell7_complete import address
        return dict(address=address(**args),execution_verified=False)
    if op=='verify_pell7_complete':
        from .pell7_complete import verify_certificate
        return dict(valid=verify_certificate(**args),execution_verified=False)
    if op=='elliptic_subgroup_index':
        from .elliptic_lattice_presentation import subgroup_index
        return subgroup_index(**args)
    if op=='verify_elliptic_subgroup_index':
        from .elliptic_lattice_verifier import verify_subgroup_index
        return dict(valid=verify_subgroup_index(**args),execution_verified=False)
    if op in {'verify_elliptic_subgroup_presentation','verify_elliptic_saturation_presentation'}:
        from .elliptic_lattice_verifier import verify_subgroup_presentation,verify_saturation_presentation
        check=verify_subgroup_presentation if op=='verify_elliptic_subgroup_presentation' else verify_saturation_presentation
        return dict(valid=check(**args),execution_verified=False)
    if op == 'verify_elliptic_subgroup_preimage':
        from .elliptic_subgroup_verifier import verify_subgroup_preimage
        return dict(valid=verify_subgroup_preimage(**args),execution_verified=False)
    if op == 'verify_elliptic_saturation':
        from .elliptic_saturation_verifier import verify_saturation
        return dict(valid=verify_saturation(**args),execution_verified=False)
    if op == 'legendre_endpoint':
        from .legendre_endpoint import endpoint_packet
        return endpoint_packet(**args)
    if op == 'verify_legendre_endpoint':
        from .legendre_endpoint import verify_endpoint
        return dict(valid=verify_endpoint(**args),execution_verified=False)
    if op == 'population_certificate':
        from .native_population_certificate import population_certificate
        return population_certificate(**args)
    if op == 'verify_marked_legendre_monodromy':
        from .period_matrix_balls import verify_marked_legendre_monodromy
        return dict(valid=verify_marked_legendre_monodromy(**args), execution_verified=False)
    if op in {'inverse_matrix_ball','multiply_matrix_balls','recognize_integral_matrix','marked_legendre_monodromy'}:
        from .period_matrix_balls import inverse_matrix_ball,multiply_matrix_balls,recognize_integral_matrix,marked_legendre_monodromy
        operations=dict(inverse_matrix_ball=inverse_matrix_ball,multiply_matrix_balls=multiply_matrix_balls,
                        recognize_integral_matrix=recognize_integral_matrix,marked_legendre_monodromy=marked_legendre_monodromy)
        return operations[op](**args)
    if op in {'cluster_graph_metric','verify_cluster_graph_metric'}:
        from .cluster_graph_metric import cluster_graph_metric,verify_cluster_graph_metric
        return (cluster_graph_metric if op=='cluster_graph_metric' else verify_cluster_graph_metric)(**args)
    if op=='factorial_window_obstruction':
        from .gamma_arithmetic import factorial_window_obstruction
        return factorial_window_obstruction(**args)
    if op in {'genus_three_tower','richelot','formal_two_isogeny','branch_braid','reflection_kernel','root_clusters','simultaneous_nodes','certified_transport','marked_legendre','frobenius','zeta','frobenius_deformation','tower_frobenius','sunrise'}:
        from .curve_correspondences import genus_three_elliptic_tower,richelot_correspondence
        from .formal_isogenies import elliptic_two_isogeny
        from .marked_curve_topology import braid_monodromy,reflection_kernel
        from .root_cluster_geometry import cluster_geometry,simultaneous_quadratic_nodes
        from .certified_period_transport import certified_transport,legendre_marked_periods
        from .arithmetic_frobenius import frobenius_matrix,zeta_by_counting,frobenius_deformation,tower_frobenius
        from .sunrise_relative import sunrise_certificate
        operations=dict(genus_three_tower=genus_three_elliptic_tower,richelot=richelot_correspondence,formal_two_isogeny=elliptic_two_isogeny,
          branch_braid=braid_monodromy,reflection_kernel=reflection_kernel,root_clusters=cluster_geometry,simultaneous_nodes=simultaneous_quadratic_nodes,
          certified_transport=certified_transport,marked_legendre=legendre_marked_periods,frobenius=frobenius_matrix,zeta=zeta_by_counting,
          frobenius_deformation=frobenius_deformation,tower_frobenius=tower_frobenius,sunrise=sunrise_certificate)
        return operations[op](**args)
    if op == 'discover_quotients':
        from .elliptic_quotients import discover_elliptic_quotients
        return discover_elliptic_quotients(request['specification'])
    if op == 'construct_quotient':
        from .elliptic_quotients import translated_even_specification
        return dict(kind='elliptic_quotient',specification=translated_even_specification(**args))
    if op == 'projective_deformation':
        from .projective_deformation import projective_deformation
        return projective_deformation(request['specification'], **args)
    if op == 'discover_rational_quotients':
        from .rational_curve_quotients import discover_rational_quotients
        return discover_rational_quotients(request['specification'], **args)
    if op == 'verify_rational_quotient':
        from .rational_curve_quotients import verify_rational_quotient
        return verify_rational_quotient(request['specification'], **args)
    if op == 'cycle_map':
        from .integral_cycle_maps import simplicial_cycle_map
        return simplicial_cycle_map(**args)
    if op == 'tensor_primitive':
        from .differential_extensions import DifferentialExtension,tensor_primitive
        left=DifferentialExtension(args['left']);right=DifferentialExtension(args['right'])
        return tensor_primitive(left.algebra,right.algebra,args.get('candidate_limit',32))
    if op == 'join':
        return catalogue.join(request['object'], request['other'], **args)
    if op == 'symbolic_join':
        from .projected_populations import symbolic_join
        if any(catalogue.definition(r)['kind']!='population' for r in (request['object'],request['other'])):raise ValueError('symbolic join requires population objects')
        derived=symbolic_join(catalogue.get(request['object']),catalogue.get(request['other']),**args)
        return catalogue.register('population',derived.specification,request.get('name'))
    definition = catalogue.definition(request['object'])
    obj = catalogue.get(request['object'])
    if op == 'restrict' and definition['kind'] == 'population':
        derived = obj.restrict(request['predicate'])
        return catalogue.register('population', derived.specification, request.get('name'))
    if op == 'compare' and definition['kind'] == 'sequence':
        if catalogue.definition(request['other'])['kind'] != 'sequence':
            raise ValueError('comparison requires sequences')
        return obj.compare(catalogue.get(request['other']), **args)
    if op == 'reweight' and definition['kind'] == 'graph':
        derived, proof = obj.with_weights(args['weights'])
        specification = dict(definition['specification'], weights=[str(w) for w in derived.measure.weights])
        return dict(object=catalogue.register('graph', specification, request.get('name')), proof=proof)
    if op != 'call' or request.get('method') not in METHODS[definition['kind']]:
        raise ValueError('unsupported operation for object kind')
    return getattr(obj, request['method'])(**args)


def serve(catalogue, source, destination, *, request_byte_limit=1000000):
    """Read bounded lines, drain overlong ones, continue after invalid requests."""
    if type(request_byte_limit) is not int or not 1 <= request_byte_limit <= 1000000:
        raise ValueError('request byte limit 1 through 1000000 required')
    while True:
        line = source.readline(request_byte_limit+1)
        if not line:
            return
        request_id = None
        try:
            overlong = len(line.encode('utf-8')) > request_byte_limit
            if len(line) > request_byte_limit and not line.endswith('\n'):
                while line and not line.endswith('\n'):
                    line = source.readline(request_byte_limit+1)
            if overlong:
                raise WorkLimit('request exceeds byte budget')
            request = json.loads(line)
            if isinstance(request, dict):
                request_id = request.get('request_id')
            answer = dispatch(catalogue, request)
            result = dict(schema='pp-query-response/1', request_id=request_id, ok=True, result=answer)
        except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, WorkLimit, RecursionError) as error:
            result = dict(schema='pp-query-response/1', request_id=request_id, ok=False,
                          error=dict(type=type(error).__name__, message=str(error)))
        destination.write(encoded(result)+'\n'); destination.flush()


def add_commands(sub):
    p = sub.add_parser('service', help='persistent exact object catalogue over JSONL stdin/stdout')
    p.add_argument('--database', required=True)
    p.add_argument('--http-port',type=int,help='serve the local HTTP console on this port (0 selects a free port)')


def cli(args):
    if args.command != 'service':
        return False
    if args.http_port is not None:
        if not 0<=args.http_port<=65535:raise ValueError('HTTP port 0 through 65535 required')
        from .http_service import run
        run(args.database,args.http_port)
        return True
    with Catalogue(args.database) as catalogue:
        serve(catalogue, sys.stdin, sys.stdout)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--database', required=True)
    with Catalogue(parser.parse_args().database) as catalogue:
        serve(catalogue, sys.stdin, sys.stdout)
