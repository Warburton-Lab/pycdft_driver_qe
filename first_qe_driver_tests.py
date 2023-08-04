from ase import Atoms
from ase.calculators.espresso import Espresso
from ase.cell import Cell
from ase.constraints import UnitCellFilter
from ase.optimize import BFGS
from ase.io import read
from ase.io.cube import read_cube_data
from pycdft import *

import subprocess
from typing import Callable, List, Union

driver_to_use = 'QE'

class QEDriverException(Exception):
    pass

class QEDriver(DFTDriver):

    ppx_charge_density_input_template = """\
&inputpp
  prefix = '{prefix}'
  outdir = '{path}/tmp/'
  filplot = '{prefix}charge'
  plot_num = 0
  spin_component = {spin_component}
/
&plot
  nfile = 1
  filepp(1) = '{path}/{prefix}charge'
  weight(1) = 1.0
  iflag = 3
  output_format = 6
  fileout = '{path}/{prefix}.rho_new.dat'
  nx={nx}, ny={ny}, nz={nz},
/

"""
    
    def __init__(self, sample: Sample, create_espresso_calculator: Callable[[], Espresso], qe_files_path: str, qe_files_prefix: str):
        # TODO: Instead of accepting a function that creates an Espresso obj and also accepting a bunch of other stuff, 
        # simply accept a dictionary containing the parameters for Espresso, and then extract the other info needed from this dict
        # and modify the values of the dict as necessary (for example, by setting the nr1s, nr2s, nr3s values to n1, n2 and n3 of the Sample)
        super(QEDriver, self).__init__(sample)
        self.create_espresso_calculator = create_espresso_calculator
        self.qe_files_path = qe_files_path
        self.qe_files_prefix = qe_files_prefix

    def reset(self, output_path):
        print("QuantumESPRESSODriver: creating new Espresso calculator")
        self.espresso = self.create_espresso_calculator()

    # def set_Vc(self, Vc):

    def get_rho_r(self):
        vspin = self.sample.vspin
        n1, n2, n3 = self.sample.n1, self.sample.n2, self.sample.n3
        self.sample.rho_r = np.zeros([vspin, n1, n2, n3])

        for ispin in range(vspin):

            ppx_input = self.ppx_charge_density_input_template.format(
                path = self.qe_files_path,
                prefix = self.qe_files_prefix,
                spin_component = ispin+1 if vspin == 2 else 0,
                nx = n1, ny = n2, nz = n3
            )
            ppx_input_file_path = '{}/{}.pp_rho.ppi'.format(self.qe_files_path, self.qe_files_prefix)
            open(ppx_input_file_path, 'w').write(ppx_input)

            pp_process = subprocess.Popen("pp.x < {}".format(ppx_input_file_path), shell=True)

            pp_errorcode = pp_process.wait()

            if pp_errorcode:
                msg = 'pp.x execution failed with error code {} using input file {}'.format(pp_errorcode, ppx_input_file_path)
                raise QEDriverException(msg)
            
            rhor_raw = read_cube_data('{}/{}.rho_new.dat'.format(self.qe_files_path, self.qe_files_prefix))[0]
            if rhor_raw.shape != (n1, n2, n3):
                msg = 'Charge density data shape is {}, but Sample shape is {}. These must match. Make sure the nr1s, nr2s, and nr3s values used in your pw.x calculation match n1, n2 and n3 in your Sample.'.format(rhor_raw.shape, (n1, n2, n3))
                raise QEDriverException(msg)

            rhor1 = np.roll(rhor_raw, rhor_raw.shape[0]//2, axis=0)
            rhor2 = np.roll(rhor1, rhor_raw.shape[1]//2, axis=1)
            rhor3 = np.roll(rhor2, rhor_raw.shape[2]//2, axis=2)
            self.sample.rho_r[ispin] = rhor3


if driver_to_use == 'Qbox':

    cell: Union[Atoms, List[Atoms]] = read('./src/pycdft/examples/01-he2_coupling/interactive/He2_3Ang.cif')
    print("Initial atomic positions (Ang):")
    print(cell.get_positions())

    # sample = Sample(ase_cell=cell, n1=112, n2=112, n3=112, vspin=1)

    print(sample.atoms[1])

    dft_driver = QboxDriver(
        sample=sample,
        init_cmd="load gs.xml \n" 
            "set xc PBE \n" 
            "set wf_dyn PSDA \n" 
            "set_atoms_dyn CG \n" 
            "set scf_tol 1.0E-8 \n",
        scf_cmd="run 0 50 5",
    )

elif driver_to_use == 'QE':

    pseudos = {
        "He": "He.pbe-kjpaw_psl.1.0.0.UPF",
    }

    empty_cell: Cell = Cell.fromcellpar([30, 30, 30, 90, 90, 90])

    cell: Union[Atoms, List[Atoms]] = read('./src/pycdft/examples/01-he2_coupling/interactive/He2_3Ang.cif')
    cell.set_cell(empty_cell)

    sample = Sample(ase_cell=cell, n1=112, n2=112, n3=112, vspin=1)

    cell.set_initial_magnetic_moments(magmoms=2*[1])

    # nr1s, nr2s and nr3s need to be the same as n1, n2 and n3 in the Sample. If they aren't, PyCDFT won't work. 
    # However, if "bad" values for nr1s, nr2s, nr3s and ecutrho are chosen, pw.x may crash complaining about 
    # mismatching G-vectors. When ecutrho isn't specified, nr1s, nr2s and nr3s default to nr1, nr2 and nr3, so 
    # here we specify those instead.
    def create_espresso_calc() -> Espresso:
        return Espresso(
            calculation = 'scf',
            restart_mode = 'from_scratch',
            outdir = './tmp',
            prefix = 'he',
            pseudo_dir = '/mnt/pan/CSE_ECHE_REW134/rew134/share/pseudos/pslibrary.1.0.0/pbe/PSEUDOPOTENTIALS/',
            ibrav = 0,
            nat = 2,
            ntyp = 1,
            tot_charge = 1,
            ecutwfc = 45.0,
            nr1 = sample.n1,
            nr2 = sample.n2,
            nr3 = sample.n3,
            nr1s = sample.n1,
            nr2s = sample.n2,
            nr3s = sample.n3,
            input_dft = 'pbe',
            nspin = 2,
            occupations = 'smearing',
            smearing = 'gauss',
            degauss = 0.001,
            conv_thr = 1e-08,
            mixing_beta = 0.7,
            pseudopotentials = pseudos,
            k_points = 'gamma',
            command = 'mpirun -np 40 pw.x -pd .true. -ni 1 -nk 2 -nb 1 -nt 1 -nd 1 -inp espresso.pwi > espresso.pwo',
        )
    
    cell.calc = create_espresso_calc()

    # cell.calc.calculate(atoms = cell)

    dft_driver = QEDriver(
        sample=sample,
        create_espresso_calculator=create_espresso_calc,
        qe_files_path='./',
        qe_files_prefix='he'
    )

solver1 = CDFTSolver(job='scf', optimizer='brenth', sample=sample, dft_driver=dft_driver)

ChargeTransferConstraint(
    sample=solver1.sample,
    donor=Fragment(solver1.sample, solver1.sample.atoms[0:1]),
    acceptor=Fragment(solver1.sample, solver1.sample.atoms[1:2]),
    V_brak=(2,2),
    N0=1,
    N_tol=1E-6,
)

print("~~~~~~~~~~~~~~~~~~~~ Applying CDFT ~~~~~~~~~~~~~~~~~~~~")
print("---- solver A ------")
solver1.solve()
