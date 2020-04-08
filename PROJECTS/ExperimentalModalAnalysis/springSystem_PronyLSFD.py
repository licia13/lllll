# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
#                                                                              #
# Use FRF and  the eigenvalues identified with the LSCE method to compute an   #
# approximation of the modes of the system                                     #
# - IRF : impulsive respose function                                           #
# - LSCE: least-squares complex exponential (~Prony's method)                  #
#                                                                              #
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
# 

import numpy as np
import matplotlib.pyplot as plt

# === Parameters of the LSFD method ===
omMin = 10.  ; fMin = 2*np.pi * omMin
omMax = 25.  ; fMax = 2*np.pi * omMax

check = False

# === Import files ===
# freqeuncy response function ---
frffile = np.load('./data/springFRF.npz')
print('\n reading FRF file: ',frffile.files)
f = frffile['f'] ; print('f.shape: ', f.shape) # frequency
U = frffile['U'] ; print('U.shape: ', U.shape) # F(input)
X = frffile['X'] ; print('X.shape: ', X.shape) # F(state) (x,v)
H = frffile['H'] ; print('H.shape: ', H.shape) # FRF (x,v)
om = 2*np.pi * f                               # angular velocity

ndofs = int( X.shape[0] / 2 )
print(' ndofs: ', ndofs)

# impulse response function ---
irffile = np.load('./data/springIRF.npz')
print('\n reading IRF file: ',irffile.files)
t = irffile['t' ] ; print(' t.shape: ',  t.shape) # time
ht= irffile['ht'] ; print('ht.shape: ', ht.shape) # irf  

# identified eigenvalues ---
sidfile = np.load('./data/springIdEig.npz')
print('\n reading the file containing the identified eigenvalues: ', \
        sidfile.files)
s = sidfile['s']            # identified eigenvalues: s = sigma + j * om

# sort eigenvalues for increasing values of the imaginary part
isort = np.argsort( np.imag(s) )
s = s[isort]
if ( check ):
    print(' s: ') ; print(s)


nPos = int( np.floor(s.shape[0]/2) )
print(' n. of eigenvalues with positive imag part: ', nPos)

sPos = s[nPos:]
if ( check ):
    print(' sPos: ') ; print(sPos)

# === Build the overdetermined linear system for Modal Identification ===
# SIMO system: forcing in the last node only
id_f = np.array( [ ndofs-1 ] )   # Python indexing

# n. om between omMin and omMax
print(om)
om_lsfd_i = ( om >= omMin ) &  ( om <= omMax )
om_lsfd = om[om_lsfd_i]
print(om_lsfd)
n_om_lsfd = om_lsfd.shape[0]
print(' n. of om resolved in the frf between omMin and omMax: ', n_om_lsfd)
H_lsfd = H[:,om_lsfd_i]

eig_lsfd_i = ( np.imag(s) >= omMin ) &  ( np.imag(s) <= omMax )
eig_lsfd = s[eig_lsfd_i]
print(eig_lsfd)
n_eig_lsfd = eig_lsfd.shape[0]
print(' n. of eig resolved in the frf between omMin and omMax: ', n_eig_lsfd)

nin = 1
nout = ndofs
Urs = np.zeros( (2*n_eig_lsfd+2,nout*nin), dtype=float)
Ars = np.zeros( (n_eig_lsfd,nout*nin), dtype=complex)
rind = np.zeros( (nout*nin), dtype=int)
sind = np.zeros( (nout*nin), dtype=int)

ils = 0
for ii in range(nin):
    for io in range(nout):

        print(' input, output: %d/%d , %d/%d' % (ii+1,nin,io+1,nout) )

        # Initialise matrix and rhs
        A = np.zeros((2*n_om_lsfd, 2*n_eig_lsfd+2), dtype=float)
        B = np.zeros((2*n_om_lsfd)                , dtype=float)

        # Build matrix and rhs
        for iom in range(n_om_lsfd):
            omega = om_lsfd[iom]
            # real part -----------
            A[2*iom,0:n_eig_lsfd] = np.real( \
                    1. / ( 1j*omega - eig_lsfd ) + \
                    1. / ( 1j*omega - np.conjugate(eig_lsfd) ) )
            A[2*iom,n_eig_lsfd:2*n_eig_lsfd] = np.real( \
                   1.j / ( 1j*omega - eig_lsfd ) - \
                   1.j / ( 1j*omega - np.conjugate(eig_lsfd) ) )
            A[2*iom,2*n_eig_lsfd] = 1.
            A[2*iom,2*n_eig_lsfd+1] = - 1. / omega**2.
            B[2*iom] = np.real( H_lsfd[io,iom] )
            # imag part -----------
            A[2*iom+1,0:n_eig_lsfd] = np.imag( \
                      1. / ( 1j*omega - eig_lsfd ) + \
                      1. / ( 1j*omega - np.conjugate(eig_lsfd) ) )
            A[2*iom+1,n_eig_lsfd:2*n_eig_lsfd] = np.imag( \
                     1.j / ( 1j*omega - eig_lsfd ) - \
                     1.j / ( 1j*omega - np.conjugate(eig_lsfd) ) )
            A[2*iom+1,2*n_eig_lsfd] = 0.
            A[2*iom+1,2*n_eig_lsfd+1] = 0.
            B[2*iom+1] = np.imag( H_lsfd[io,iom] )

        print(' A: ') ; print(A)

        # Solve the linear system in the LS sense
        x, resid, rank, s = np.linalg.lstsq(A,B, rcond=-1)
#       print(' x.shape: ', x.shape)
#       print(' x: ' , x)
        # Collect solution
        Urs[:,ils] = x
        Ars[:,ils] = x[0:n_eig_lsfd] + 1j * x[n_eig_lsfd:2*n_eig_lsfd]
        print(' Ars[:,%d]: ' % (ils)) ; print(Ars[:,ils])
        rind[ils] = io
        sind[ils] = ii

        ils += 1
print(' Ars: ') ; print(Ars)

# === Mode reconstruction ===
Z = np.zeros((nout, n_eig_lsfd), dtype=complex)
ii = 1
for ik in range(n_eig_lsfd):
    Z[id_f,ik] = np.sqrt( Ars[ik,id_f] )
    for io in range(nout):
        if ( not io == id_f ):
            Z[io,ik] = Ars[ik,io] / Z[id_f,ik]

# check ----
# print(' Ars[4,4]: ', Ars[4,4])
# print(' np.sqrt(Ars[4,4]): ', np.sqrt(Ars[4,4]))
# print(' Z: ') ; print(Z)

# add phase (~normalisation)
dphi = np.angle( Z[0,:] )
Z = Z * np.exp( -1.j * dphi ) # broadcasting

plt.figure(501, figsize=(3,9))
for ip in range(n_eig_lsfd):
    plt.subplot(n_eig_lsfd,1,ip+1)
    plt.plot(np.real(Z[:,ip])), plt.plot(np.imag(Z[:,ip]))
    plt.title('s=%8.3f+j%8.3f' % (np.real(eig_lsfd[ip]),np.imag(eig_lsfd[ip])) )
    plt.grid(True) 


plt.show()




