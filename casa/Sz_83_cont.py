#!/usr/bin/env

"""

split, clean, and self-cal continuum and line data
  
NOTE: this is intended to be an interactive, iterative process
      so this is more a log that should be run by cutting and
      pasting into casa rather than as an executable script

      search "CHANGEME" for variables to be changed
      
10/9/15 MCA

"""



# ======================== Setup ===========================


# LupusIII_1005  15:56:42.310 -37:49:15.499
# Class II, K7
# Companion below source?


field = 21                                     # CHANGEME 

file_ms = '../science_calibrated.ms'
contspw   = '2,3,4'
contspw_w = [128,3840,1920] 

robust     = 0.5                               # CHANGEME
imsize     = [640,640]
cell       = '0.03arcsec'
imagermode = 'csclean'
refant     = 'DA52'                            # CHANGEME

xc         = 326                               # CHANGEME
yc         = 309                               # CHANGEME
in_a       = 80
out_a      = 120
aper       = 1.25

boxwidth = 300.
box = rg.box([xc-boxwidth,yc-boxwidth],[xc+boxwidth,yc+boxwidth])


# ======================= Split Off Continuum ========================


# split off field from full ms
split(vis = file_ms,
      outputvis = 'f'+str(field)+'.vis',
      field = field,
      datacolumn = 'data')

# split off continuum (take the large bw spw and average
split(vis = 'f'+str(field)+'.vis',
      outputvis = 'f'+str(field)+'_cont.vis',
      spw = contspw,
      width = contspw_w,
      datacolumn = 'data')

# plot uv-distance vs. amplitude
plotms(vis='f'+str(field)+'_cont.vis',
       xaxis='uvdist',yaxis='amp',
       coloraxis='spw')
       # plotfile='f'+str(field)+'_ampuv_orig.png'
       # showgui=False,
       # highres=True,
       # overwrite=True)
# source is very resolved

# find antenna close to center of configuration
# check pipeline log that this ant is OK
plotants(vis='f'+str(field)+'_cont.vis') #, figfile='f'+str(field)+'_ants.png')



                        
# ================== Clean continuum before selfcal ==================

# os.system('rm -rf f'+str(field)+'_cont_b4sc*')

# light clean (100 iterations) to set the mask around the main peaks
clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_b4sc',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 100,
      threshold = '0.0mJy',
      interactive = True,
      mask = '',
      cell = cell,
      imsize = imsize,
      weighting = 'briggs',
      robust = robust,
      imagermode = imagermode)

im_max = imstat(imagename = 'f'+str(field)+'_cont_b4sc.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_b4sc.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
# Peak = 169.34 mJy, rms = 1.16 mJy, S/N = 145.4


        
# ======================== Self-Calibrate 1 ==================

# first combine all the data by time (solint = inf)
# i.e., phase self-cal over entire integration time
gaincal(vis = 'f'+str(field)+'_cont.vis',
        caltable = 'f'+str(field)+'_cont_pcal1',
        refant = refant,
        solint = 'inf',
        combine = 'spw',
        gaintype = 'T',
        spw = '',
        calmode = 'p',
        minblperant = 4,
        minsnr = 3)

# plot phase for each antenna
plotcal(caltable = 'f'+str(field)+'_cont_pcal1',
        xaxis = 'time',
        yaxis = 'phase',
        spw = '',
        iteration = 'antenna',
        subplot = 421,
        plotrange = [0,0,-200,200]) # narrow yrange phases close to zero
# no variation between integration times (expected since solin=inf)
# note DV02 has no data (100% flagged in pipeline calibration)


# apply calibration to data
applycal(vis = 'f'+str(field)+'_cont.vis',
        spw = '',
        gaintable = ['f'+str(field)+'_cont_pcal1'],
        spwmap = [0,0,0],
        calwt = T,
        flagbackup = F)

# clean self-calibrated data
clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_pcal1_clean',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 100,
      threshold   = '0.0mJy',
      interactive = False,
      mask = 'f'+str(field)+'_cont_b4sc.mask',
      cell        = cell,
      imsize      = imsize,
      weighting   = 'briggs',
      robust      = robust,
      imagermode  = imagermode)

im_max = imstat(imagename = 'f'+str(field)+'_cont_pcal1_clean.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_pcal1_clean.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
# Peak = 176.60 mJy, rms = 0.58 mJy, S/N = 306.9 (huge improvement)

# inspect images
imview(raster=[{'file':'f'+str(field)+'_cont_b4sc.image'},
               {'file':'f'+str(field)+'_cont_pcal1_clean.image'}])
# much cleaner image





# ======================== Self-Calibrate 2 ==================

# decrease phase self-cal solution interval to a few times integration time
# int = 6s (from X125.log)
gaincal(vis = 'f'+str(field)+'_cont.vis',
        caltable = 'f'+str(field)+'_cont_pcal2',
        refant = refant,
        solint = '20s',                           # CHANGEME
        combine = 'spw',
        gaintype = 'T',
        spw = '',
        calmode = 'p',
        minblperant = 4,
        minsnr = 3)

plotcal(caltable = 'f'+str(field)+'_cont_pcal2',
        xaxis = 'time',
        yaxis = 'phase',
        spw = '',
        iteration = 'antenna',
        subplot = 421,
        plotrange = [0,0,-200,200])

applycal(vis = 'f'+str(field)+'_cont.vis',
        spw = '',
        gaintable = ['f'+str(field)+'_cont_pcal2'],
        spwmap = [0,0,0],
        calwt = T,
        flagbackup = F)

clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_pcal2_clean',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 100,
      threshold   = '0.0mJy',
      interactive = False,
      mask = 'f'+str(field)+'_cont_b4sc.mask',
      cell        = cell,
      imsize      = imsize,
      weighting   = 'briggs',
      robust      = robust,
      imagermode  = imagermode)

im_max = imstat(imagename = 'f'+str(field)+'_cont_pcal2_clean.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_pcal2_clean.image', region='annulus[[320pix,320pix],[60pix,100pix]]')['rms'][0]
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
# Peak = 176.62 mJy, rms = 0.55 mJy, S/N = 320.4 (slight improvement from pcal1)

# inspection of the image shows no change from pcal1
imview(raster=[{'file':'f'+str(field)+'_cont_b4sc.image'},
               {'file':'f'+str(field)+'_cont_pcal1_clean.image'},
               {'file':'f'+str(field)+'_cont_pcal2_clean.image'}])
# looks the same




# ======================== Self-Calibrate 3 ==================

# try smallest possible solution interval = integration time
# 1 of 40 solutions flagged due to SNR < 3 in spw=0
gaincal(vis = 'f'+str(field)+'_cont.vis',
        caltable = 'f'+str(field)+'_cont_pcal3',
        refant = refant,
        solint = 'int',
        combine = 'spw',
        gaintype = 'T',
        spw = '',
        calmode = 'p',
        minblperant = 4,
        minsnr = 3)

# can now see the individual integrations within the two visits to target
# and there is scatter from one point to the next => intrinsic phase noise
plotcal(caltable = 'f'+str(field)+'_cont_pcal3',
        xaxis = 'time',
        yaxis = 'phase',
        spw = '',
        iteration = 'antenna',
        subplot = 421,
        plotrange = [0,0,-200,200])

applycal(vis = 'f'+str(field)+'_cont.vis',
        spw = '',
        gaintable = ['f'+str(field)+'_cont_pcal3'],
        spwmap = [0,0,0],
        calwt = T,
        flagbackup = F)

clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_pcal3_clean',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 100,
      threshold   = '0.0mJy',
      interactive = False,
      mask = 'f'+str(field)+'_cont_b4sc.mask',
      cell        = cell,
      imsize      = imsize,
      weighting   = 'briggs',
      robust      = robust,
      imagermode  = imagermode)

im_max = imstat(imagename = 'f'+str(field)+'_cont_pcal3_clean.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_pcal3_clean.image', region='annulus[[320pix,320pix],[60pix,100pix]]')['rms'][0]
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
# Peak = 176.91 mJy, rms = 0.55 mJy, S/N = 321.4 (no change from pcal2)


# inspection of the image shows first peak strengthening again, so will use this one
imview(raster=[{'file':'f'+str(field)+'_cont_b4sc.image'},
               {'file':'f'+str(field)+'_cont_pcal1_clean.image'},
               {'file':'f'+str(field)+'_cont_pcal2_clean.image'},
               {'file':'f'+str(field)+'_cont_pcal3_clean.image'}])
# pcals all look similar





# ======================== Best Continuum Map ==================


# so now run the same applycal but with flagbackup = T,
applycal(vis = 'f'+str(field)+'_cont.vis',
        spw = '',
        gaintable = ['f'+str(field)+'_cont_pcal2'],         # CHANGEME
        spwmap = [0,0,0],
        calwt = T,
        flagbackup = T)

# deep clean, trying different robust weights
clean(vis = 'f'+str(field)+'_cont.vis',
      imagename = 'f'+str(field)+'_cont_best',
      mode = 'mfs',
      psfmode = 'clark',
      niter = 2000,
      threshold   = '0.0mJy',
      interactive = True,
      mask = '',
      cell        = cell,
      imsize      = imsize,
      weighting   = 'briggs',
      robust      = -1,                                      # CHANGEME
      imagermode  = imagermode)
# placed mask slightly larger than outer continuum contour
# stopped after 500 iterations once the inside became green


im_max = imstat(imagename = 'f'+str(field)+'_cont_best.image')['max'][0]
im_rms = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
bmaj = imhead(imagename = 'f'+str(field)+'_cont_best.image', mode="get", hdkey="beammajor")
bmin = imhead(imagename = 'f'+str(field)+'_cont_best.image', mode="get", hdkey="beamminor")
print 'Peak = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_max, 1000*im_rms, im_max/im_rms)
print 'Beam = {0:.2f} x {1:.2f} arcsec'.format(bmaj.get('value'),bmin.get('value'))

# robust = -1 
# Peak = 165.88 mJy, rms = 0.56 mJy, S/N = 295.1
# Beam = 0.33 x 0.27 arcsec


# save this to a fits file
exportfits(imagename='f'+str(field)+'_cont_best.image', fitsimage='f'+str(field)+'_cont.fits')

# compare to before self-cal
imview(raster=[{'file':'f'+str(field)+'_cont_b4sc.image'},
               {'file':'f'+str(field)+'_cont_best.image'}])

# measure flux
# imview(raster=[{'file':'f'+str(field)+'_cont_best.image'}])
im_rms = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                region='annulus[['+str(xc)+'pix,'+str(yc)+'pix],['+str(in_a)+'pix,'+str(out_a)+'pix]]')['rms'][0]
im_flux = imstat(imagename = 'f'+str(field)+'_cont_best.image',
                 region='circle[['+str(xc)+'pix,'+str(yc)+'pix],'+str(aper)+'arcsec]')['flux'][0]
print 'Flux = {0:.2f} mJy, rms = {1:.2f} mJy, S/N = {2:.1f}'.format(1000*im_flux, 1000*im_rms, im_flux/im_rms)
# Flux = 432.19 mJy, rms = 0.56 mJy, S/N = 768.9

# re-center image on source and use get_flux.py to get COG flux
ia.fromimage(outfile = 'f'+str(field)+'_cont_cropped.image',
             infile  = 'f'+str(field)+'_cont.fits',
             region  = box )
ia.close() 
exportfits(imagename = 'f'+str(field)+'_cont_cropped.image',
           fitsimage = 'f'+str(field)+'_cont_cropped.fits')




# ======================== Measure flux with UVMODELFIT ==================

# calculate offset from phase center in arcsec
pixscale = 0.03             # must match 'cell'                 
dx = pixscale*(320.0-xc)    # offset to east (left)
dy = pixscale*(yc-320.0)    # offset to north (up)

  
# measure flux as gaussian
uvmodelfit(vis       = 'f'+str(field)+'_cont.vis',
           comptype  = 'G',
           sourcepar = [im_flux,dx,dy,0.5,1,0],
           varypar   = [T,T,T,T,T,T],
           niter     = 10)

'''

reduced chi2=1.732
I = 0.426896 +/- 0.000722033
x = -0.176817 +/- 0.000338048 arcsec
y = -0.328364 +/- 0.000321827 arcsec
a = 0.378682 +/- 0.000884277 arcsec
r = 1 +/- 0.00346183
p = 0 +/- 57.2958 deg

consistent with aperture method
15:56:42.295 -37:49:15.828
'''
