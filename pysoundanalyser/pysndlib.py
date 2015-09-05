# -*- coding: utf-8 -*-

#   Copyright (C) 2008-2015 Samuele Carcagno <sam.carcagno@gmail.com>
#   This file is part of sndlib

#    sndlib is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    sndlib is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with sndlib.  If not, see <http://www.gnu.org/licenses/>.

"""
A module for generating sounds in python.
"""

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals
import copy, numpy, multiprocessing, warnings
from numpy import array, ceil, cumsum, floor, log, sin, cos, pi, sqrt, abs, arange, zeros, ones, mean, convolve, angle, real, log2, int_, linspace, repeat, logspace, concatenate
from numpy.fft import rfft, irfft, fft, ifft
from scipy.signal import firwin2


def addSounds(snd1, snd2, delay, fs):
    """
    Add or concatenate two sounds.

    Parameters
    ----------
    snd1 : array of floats
        First sound.
    snd2 : array of floats
        Second sound.
    delay : float
        Delay in milliseconds between the onset of 'snd1' and the onset of 'snd2'
    fs : float
        Sampling frequency in hertz of the two sounds.

    Returns
    -------
    snd : 2-dimensional array of floats
       
    Examples
    --------
    >>> snd1 = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> snd2 = pureTone(frequency=880, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> snd = addSounds(snd1=snd1, snd2=snd2, delay=100, fs=48000)
    """
  
    #delay in ms
    delay = delay / 1000. #convert from ms to sec

    nSnd1 = len(snd1[:,1])
    nSnd2 = len(snd2[:,1])
    snd1Duration = nSnd1/fs
    snd2Duration = nSnd2/fs

    #------------------------
    #            ...............................

    # Seg1           Seg2              Seg3
    
    nSampSeg1 = round(delay * fs)
    if nSampSeg1 < nSnd1:
        nSampSeg2 = nSnd1 - nSampSeg1
        nSampSeg3 = nSnd2 - nSampSeg2
        seg1 = snd1[0:nSampSeg1,:]
        seg2a = snd1[nSampSeg1:nSnd1,:]
        if nSampSeg2 > nSnd2: # snd2 shorter than seg2, fill with zeros
            ldiff = nSampSeg2 - nSnd2
            diffSeg = zeros((ldiff, 2))
            seg2b = concatenate((snd2, diffSeg), axis=0)
        else:
            seg2b = snd2[0:nSampSeg2,:]
            seg3 = snd2[nSampSeg2:nSnd2,:]

        seg2 = seg2a+seg2b
        snd = concatenate((seg1, seg2), axis=0)

        if nSampSeg2 < nSnd2:
            snd = concatenate((snd, seg3), axis=0)
            
    else:
        seg1 = snd1
        seg2 = makeSilence((delay - snd1Duration)*1000, fs)
        seg3 = snd2
        snd = concatenate((seg1, seg2), axis=0)
        snd = concatenate((snd, seg3), axis=0)
        
    return(snd)



def AMTone(frequency, AMFreq, AMDepth, phase, level, duration, ramp, channel, fs, maxLevel):
    """
    Generate an amplitude modulated tone.

    Parameters
    ----------
    frequency : float
        Carrier frequency in hertz.
    AMFreq : float
        Amplitude modulation frequency in Hz.
    AMDepth : float
        Amplitude modulation depth (a value of 1
        corresponds to 100% modulation). 
    phase : float
        Starting phase in radians.
    level : float
        Tone level in dB SPL. 
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
       
    Examples
    --------
    >>> snd = AMTone(frequency=1000, AMFreq=20, AMDepth=1, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Both', fs=48000, maxLevel=100)
    
    """

    amp = 10**((level - maxLevel) / 20)
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0., nTot) / fs
    timeRamp = arange(0., nRamp) 

    snd = zeros((nTot, 2))

    if channel == "Right":
        snd[0:nRamp, 1] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[0:nRamp])) * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 1] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp:nRamp+nSamples])) * sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 1] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp+nSamples:len(timeAll)])) * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[0:nRamp])) * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp:nRamp+nSamples])) * sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp+nSamples:len(timeAll)])) * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Both":
        snd[0:nRamp, 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[0:nRamp])) * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp:nRamp+nSamples])) * sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 0] = amp * (1 + AMDepth*sin(2*pi*AMFreq*timeAll[nRamp+nSamples:len(timeAll)])) * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
        snd[:, 1] = snd[:, 0] 
       
    return snd

def binauralPureTone(frequency, phase, level, duration, ramp, channel, itd, itdRef, ild, ildRef, fs, maxLevel):
    """
    Generate a pure tone with an optional interaural time or level difference.

    Parameters
    ----------
    frequency : float
        Tone frequency in hertz.
    phase : float
        Starting phase in radians.
    level : float
        Tone level in dB SPL. If 'ild' is different than zero, this will
        be the level of the tone in the reference channel.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    itd : float
        Interaural time difference, in microseconds.
    itdRef : 'Right', 'Left' or None
        The reference channel for the 'itd'. The interaural time
        difference will be applied to the other channel with
        respect to the reference channel.
    ild : float
        Interaural level difference in dB SPL.
    ildRef : 'Right', 'Left' or None
        The reference channel for the 'ild'.
        The level of the other channel will be
        icreased of attenuated by 'ild' dB SPL
        with respect to the reference channel.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       
    Examples
    --------
    >>> itdTone = binauralPureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Both', itd=480, itdRef='Right', ild=0, ildRef=None,
    ...     fs=48000, maxLevel=100)
    >>> ildTone = binauralPureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Both', itd=0, itdRef=None, ild=-20, ildRef='Right',
    ...     fs=48000, maxLevel=100)
    
    """

    if channel not in ["Right", "Left", "Both"]:
        raise TypeError("Invalid channel argument. Channel must be one of 'Right', 'Left' or 'Both'")
    if itdRef not in ["Right", "Left", None]:
        raise TypeError("Invalid 'itdRef' argument. 'itdRef' must be one of 'Right', 'Left' or None")
    if ildRef not in ["Right", "Left", None]:
        raise TypeError("Invalid 'ildRef' argument. 'ildRef' must be one of 'Right', 'Left' or None")
    
    if itd != 0 and itdRef == None:
        warnings.warn("'itd' is different than zero but no 'itdRef' was given. No 'itd' will be applied.")
    if ild != 0 and ildRef == None:
        warnings.warn("'ild' is different than zero but no 'ildRef' was given. No 'ild' will be applied.")

    
    if channel == 'Both':
        ipd = itdtoipd(itd/1000000, frequency)
        if ildRef == 'Right':
            ampRight = 10**((level - maxLevel) / 20)
            ampLeft = 10**((level + ild - maxLevel) / 20)
        elif ildRef == 'Left':
            ampLeft = 10**((level - maxLevel) / 20)
            ampRight = 10**((level + ild - maxLevel) / 20)
        elif ildRef == None:
            ampRight = 10**((level - maxLevel) / 20)
            ampLeft = ampRight

        if itdRef == 'Right':
            phaseRight = phase
            phaseLeft = phase + ipd
        elif itdRef == 'Left':
            phaseLeft = phase
            phaseRight = phase + ipd
        elif itdRef == None:
            phaseRight = phase
            phaseLeft = phase
    else:
        amp = 10**((level - maxLevel) / 20.)
            
    duration = duration / 1000. #convert from ms to sec
    ramp = ramp / 1000.

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0., nTot) / fs
    timeRamp = arange(0., nRamp) 

    snd = zeros((nTot, 2))


    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 1] = amp* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Both":
        snd[0:nRamp, 0] = ampLeft * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phaseLeft)
        snd[nRamp:nRamp+nSamples, 0] = ampLeft* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phaseLeft)
        snd[nRamp+nSamples:len(timeAll), 0] = ampLeft * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phaseLeft)

        snd[0:nRamp, 1] = ampRight * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phaseRight)
        snd[nRamp:nRamp+nSamples, 1] = ampRight* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phaseRight)
        snd[nRamp+nSamples:len(timeAll), 1] = ampRight * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phaseRight)


    return snd


def broadbandNoise(spectrumLevel, duration, ramp, channel, fs, maxLevel):
    """
    Synthetise a broadband noise.

    Parameters
    ----------
    spectrumLevel : float
        Intensity spectrum level of the noise in dB SPL. 
    duration : float
        Noise duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the noise will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       
    Examples
    --------
    >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
    ...     channel='Both', fs=48000, maxLevel=100)
    
    """
    """ Comments:.
    The intensity spectrum level in dB is SL
    The peak amplitude A to achieve a desired SL is
    SL = 10*log10(RMS^2/NHz) that is the total RMS^2 divided by the freq band
    SL/10 = log10(RMS^2/NHz)
    10^(SL/10) = RMS^2/NHz
    RMS^2 = 10^(SL/10) * NHz
    RMS = 10^(SL/20) * sqrt(NHz)
    NHz = sampRate / 2 (Nyquist)
    

    """
    amp = sqrt(fs/2)*(10**((spectrumLevel - maxLevel) / 20))
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 

    snd = zeros((nTot, 2))
    #random is a numpy module
    noise = (numpy.random.random(nTot) + numpy.random.random(nTot)) - (numpy.random.random(nTot) + numpy.random.random(nTot))
    RMS = sqrt(mean(noise*noise))
    #scale the noise so that the maxAmplitude goes from -1 to 1
    #since A = RMS*sqrt(2)
    scaled_noise = noise / (RMS * sqrt(2))


    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * scaled_noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1] = amp * scaled_noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * scaled_noise[nRamp+nSamples:len(timeAll)]
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * scaled_noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0] = amp * scaled_noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * scaled_noise[nRamp+nSamples:len(timeAll)]
    elif channel == "Both":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * scaled_noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1] = amp * scaled_noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * scaled_noise[nRamp+nSamples:len(timeAll)]
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * scaled_noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0] = amp * scaled_noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * scaled_noise[nRamp+nSamples:len(timeAll)]
    return snd


def chirp(freqStart, ftype, rate, level, duration, phase, ramp, channel, fs, maxLevel):
    """
    Synthetize a chirp, that is a tone with frequency changing linearly or
    exponentially over time with a give rate.
    

    Parameters
    ----------
    freqStart : float
        Starting frequency in hertz.
    ftype : string
        If 'linear', the frequency will change linearly on a Hz scale.
        If 'exponential', the frequency will change exponentially on a cents scale.
    rate : float
        Rate of frequency change, Hz/s if ftype is 'linear',
        and cents/s if ftype is 'exponential'.
    level : float
        Level of the tone in dB SPL.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       
    Examples
    --------
    >>> gl = chirp(freqStart=440, ftype='linear', rate=500, level=55,
            duration=980, phase=0, ramp=10, channel='Both',
            fs=48000, maxLevel=100)

    """
    
    amp = 10**((level - maxLevel) / 20)
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000
    totDur = duration+ramp*2
    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)
    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp)
    if ftype == "exponential":
        k = 2**(rate/1200)
        frequency = freqStart*( ( ( (k**timeAll) - 1) /log(k) + phase) )
    elif ftype == "linear":
        frequency = freqStart*timeAll + (rate/2)*timeAll**2 + phase
        

    snd = zeros((nTot, 2))

    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[0:nRamp] )
        snd[nRamp:nRamp+nSamples, 1] = amp* sin(2*pi*frequency[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[nRamp+nSamples:len(timeAll)])
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[0:nRamp] )
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*frequency[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[nRamp+nSamples:len(timeAll)])
    elif channel == "Both":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[0:nRamp] )
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*frequency[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency[nRamp+nSamples:len(timeAll)])
        snd[:, 1] = snd[:, 0] 

    return snd


def complexTone(F0, harmPhase, lowHarm, highHarm, stretch, level, duration, ramp, channel, fs, maxLevel):
    """
    Synthetise a complex tone.

    Parameters
    ----------
    F0 : float
        Tone fundamental frequency in hertz.
    harmPhase : one of 'Sine', 'Cosine', 'Alternating', 'Random', 'Schroeder'
        Phase relationship between the partials of the complex tone.
    lowHarm : int
        Lowest harmonic component number.
    highHarm : int
        Highest harmonic component number.
    stretch : float
        Harmonic stretch in %F0. Increase each harmonic frequency by a fixed value
        that is equal to (F0*stretch)/100. If 'stretch' is different than
        zero, an inhanmonic complex tone will be generated.
    level : float
        The level of each partial in dB SPL.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : 'Right', 'Left', 'Both', 'Odd Right' or 'Odd Left'
        Channel in which the tone will be generated. If 'channel'
        if 'Odd Right', odd numbered harmonics will be presented
        to the right channel and even number harmonics to the left
        channel. The opposite is true if 'channel' is 'Odd Left'.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).

    Examples
    --------
    >>> ct = complexTone(F0=440, harmPhase='Sine', lowHarm=3, highHarm=10,
    ...     stretch=0, level=55, duration=180, ramp=10, channel='Both',
    ...     fs=48000, maxLevel=100)
    
    """
    amp = 10**((level - maxLevel) / 20)
    duration = duration / 1000. #convert from ms to sec
    ramp = ramp / 1000
    stretchHz = (F0*stretch)/100
    
    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)
    
    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 

    snd = zeros((nTot, 2))
    if channel == "Right" or channel == "Left" or channel == "Both":
        tone = zeros(nTot)
    elif channel == "Odd Left" or channel == "Odd Right":
        toneOdd = zeros(nTot)
        toneEven = zeros(nTot)

    if harmPhase == "Sine":
        for i in range(lowHarm, highHarm+1):
            if channel == "Right" or channel == "Left" or channel == "Both":
                tone =  tone + sin(2 * pi * ((F0 * i) + stretchHz) * timeAll)
            elif channel == "Odd Left" or channel == "Odd Right":
                if i%2 > 0: #odd harmonic
                    toneOdd = toneOdd + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll)
                else:
                    toneEven = toneEven + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll)
    elif harmPhase == "Cosine":
        for i in range(lowHarm, highHarm+1):
            if channel == "Right" or channel == "Left" or channel == "Both":
                tone = tone + cos(2 * pi * ((F0 * i)+stretchHz) * timeAll)
            elif channel == "Odd Left" or channel == "Odd Right":
                if i%2 > 0: #odd harmonic
                    toneOdd = toneOdd + cos(2 * pi * ((F0 * i)+stretchHz) * timeAll)
                else:
                    toneEven = toneEven + cos(2 * pi * ((F0 * i)+stretchHz) * timeAll)
    elif harmPhase == "Alternating":
        for i in range(lowHarm, highHarm+1):
            if i%2 > 0: #odd harmonic
                if channel == "Right" or channel == "Left" or channel == "Both":
                    tone = tone + cos(2 * pi * ((F0 * i)+stretchHz) * timeAll)
                elif channel == "Odd Left" or channel == "Odd Right":
                    toneOdd = toneOdd + cos(2 * pi * ((F0 * i)+stretchHz) * timeAll)
            else: #even harmonic
                if channel == "Right" or channel == "Left" or channel == "Both":
                    tone = tone + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll)
                elif channel == "Odd Left" or channel == "Odd Right":
                    toneEven = toneEven + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll)
    elif harmPhase == "Schroeder":
        for i in range(lowHarm, highHarm+1):
            phase = -pi * i * (i - 1) / float(highHarm)
            if channel == "Right" or channel == "Left" or channel == "Both":
                tone = tone + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)
            elif channel == "Odd Left" or channel == "Odd Right":
                if i%2 > 0: #odd harmonic
                    toneOdd = toneOdd + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)
                else:
                    toneEven = toneEven + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)
    elif harmPhase == "Random":
        for i in range(lowHarm, highHarm+1):
            phase = numpy.random.random() * 2 * pi
            if channel == "Right" or channel == "Left" or channel == "Both":
                tone = tone + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)
            elif channel == "Odd Left" or channel == "Odd Right":
                if i%2 > 0: #odd harmonic
                    toneOdd = toneOdd + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)
                else:
                    toneEven = toneEven + sin(2 * pi * ((F0 * i)+stretchHz) * timeAll + phase)


    if channel == "Right":
        snd[0:nRamp, 1]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) * tone[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1]        = amp * tone[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * tone[nRamp+nSamples:len(timeAll)]
    elif channel == "Left":
        snd[0:nRamp, 0]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) *  tone[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0]        = amp * tone[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * tone[nRamp+nSamples:len(timeAll)]
    elif channel == "Both":
        snd[0:nRamp, 0]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) *  tone[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0]        = amp * tone[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * tone[nRamp+nSamples:len(timeAll)]
        snd[:, 1] = snd[:, 0]
    elif channel == "Odd Left":
        snd[0:nRamp, 0]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) *  toneOdd[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0]        = amp * toneOdd[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * toneOdd[nRamp+nSamples:len(timeAll)]
        snd[0:nRamp, 1]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) * toneEven[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1]        = amp * toneEven[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * toneEven[nRamp+nSamples:len(timeAll)]
    elif channel == "Odd Right":
        snd[0:nRamp, 1]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) *  toneOdd[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1]        = amp * toneOdd[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * toneOdd[nRamp+nSamples:len(timeAll)]
        snd[0:nRamp, 0]                     = amp * ((1-cos(pi * timeRamp/nRamp))/2) * toneEven[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0]        = amp * toneEven[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * toneEven[nRamp+nSamples:len(timeAll)]
        

    return snd


def complexToneParallel(F0, harmPhase, lowHarm, highHarm, stretch, level, duration, ramp, channel, fs, maxLevel):
    """
    Synthetise a complex tone.

    This function produces the same results of complexTone. The only difference
    is that it uses the multiprocessing Python module to exploit multicore
    processors and compute the partials in a parallel fashion. Notice that
    there is a substantial overhead in setting up the parallel computations.
    This means that for relatively short sounds (in the order of seconds),
    this function will actually be *slower* than complexTone.

    Parameters
    ----------
    F0 : float
        Tone fundamental frequency in hertz.
    harmPhase : one of 'Sine', 'Cosine', 'Alternating', 'Random', 'Schroeder'
        Phase relationship between the partials of the complex tone.
    lowHarm : int
        Lowest harmonic component number.
    highHarm : int
        Highest harmonic component number.
    stretch : float
        Harmonic stretch in %F0. Increase each harmonic frequency by a fixed value
        that is equal to (F0*stretch)/100. If 'stretch' is different than
        zero, an inhanmonic complex tone will be generated.
    level : float
        The level of each partial in dB SPL.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : 'Right', 'Left', 'Both', 'Odd Right' or 'Odd Left'
        Channel in which the tone will be generated. If 'channel'
        if 'Odd Right', odd numbered harmonics will be presented
        to the right channel and even number harmonics to the left
        channel. The opposite is true if 'channel' is 'Odd Left'.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).

    Examples
    --------
    >>> ct = complexTone(F0=440, harmPhase='Sine', lowHarm=3, highHarm=10,
    ...     stretch=0, level=55, duration=180, ramp=10, channel='Both',
    ...     fs=48000, maxLevel=100)
    
    """
    amp = 10**((level - maxLevel) / 20)
    durationSec = duration / 1000 #convert from ms to sec
    rampSec = ramp / 1000
    stretchHz = (F0*stretch)/100
    
    nSamples = int(round(durationSec * fs))
    nRamp = int(round(rampSec * fs))
    nTot = nSamples + (nRamp * 2)
    snd = zeros((nTot, 2))
    tn = []
    pool = multiprocessing.Pool()
    
    for i in range(lowHarm, highHarm+1):
        #Select channel
        if channel == "Right" or channel == "Left" or channel == "Both":
            thisChan = channel
        elif channel == "Odd Left" or channel == "Odd Right":
            if i%2 > 0: #odd harmonic
                if channel == "Odd Left":
                    thisChan = "Left"
                elif channel == "Odd Right":
                    thisChan = "Right"
            else: #even harmonic
                if channel == "Odd Left":
                    thisChan = "Right"
                elif channel == "Odd Right":
                    thisChan = "Left"
        #Select phase
        if harmPhase == "Sine":
            thisPhase = 0
        elif harmPhase == "Cosine":
            thisPhase = pi/2
        elif harmPhase == "Alternating":
            if i%2 > 0: #odd harmonic
                thisPhase = 0
            else:
                thisPhase = pi/2
        elif harmPhase == "Schroeder":
            thisPhase = -pi * i * (i - 1) / highHarm
        elif harmPhase == "Random":
            thisPhase =  numpy.random.random() * 2 * pi
                
        pool.apply_async(pureTone, (F0*i+stretchHz, thisPhase, level, duration, ramp, thisChan, fs, maxLevel), callback=tn.append)

    pool.close()
    pool.join()
    
    for i in range(len(tn)):
        snd = snd + tn[i]
        
    return snd

def expSinFMTone(fc, fm, deltaCents, phase, level, duration, ramp, channel, fs, maxLevel):
    """
    Generate an tone frequency modulated with an exponential sinusoid.

    Parameters
    ----------
    fc : float
        Carrier frequency in hertz. 
    fm : float
        Modulation frequency in Hz.
    deltaCents : float
        Frequency excursion in cents. The instataneous frequency of the tone
         will vary from fc**(-deltaCents/1200) to fc**(+deltaCents/1200).
    phase : float
        Starting phase in radians.
    level : float
        Tone level in dB SPL. 
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : 'Right', 'Left' or 'Both'
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of
        amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
       
    Examples
    --------
    >>> snd = expSinFMTone(fc=1000, fm=40, deltaCents=1200, phase=0, level=55, 
    ...     duration=180, ramp=10, channel='Both', fs=48000, maxLevel=100)
    
    """
  
    amp = 10**((level - maxLevel) / 20)
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp)
    fArr = 2*pi*fc*2**((deltaCents/1200)*cos(2*pi*fm*timeAll+phase))
    ang = cumsum(fArr)/fs

    snd = zeros((nTot, 2))

    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(ang[0:nRamp])
        snd[nRamp:nRamp+nSamples, 1] = amp* sin(ang[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(ang[nRamp+nSamples:len(timeAll)])
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(ang[0:nRamp])
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(ang[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(ang[nRamp+nSamples:len(timeAll)])
    elif channel == "Both":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(ang[0:nRamp])
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(ang[nRamp:nRamp+nSamples])
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(ang[nRamp+nSamples:len(timeAll)])
        snd[:, 1] = snd[:, 0]
       

    return snd

def FMTone(fc, fm, mi, phase, level, duration, ramp, channel, fs, maxLevel):
    """
    Generate a frequency modulated tone.

    Parameters
    ----------
    fc : float
        Carrier frequency in hertz. This is the frequency of the tone at fm zero crossing.
    fm : float
        Modulation frequency in Hz.
    mi : float
        Modulation index, also called beta and is equal to deltaF/fm, where
        deltaF is the maximum deviation of the instantaneous frequency from
        the carrier frequency.
    phase : float
        Starting phase in radians.
    level : float
        Tone level in dB SPL. 
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : 'Right', 'Left' or 'Both'
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of
        amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
       
    Examples
    --------
    >>> snd = FMTone(fc=1000, fm=40, mi=1, phase=0, level=55, duration=180,
    ...     ramp=10, channel='Both', fs=48000, maxLevel=100)
    
    """
  
    amp = 10**((level - maxLevel) / 20)
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 

    snd = zeros((nTot, 2))
    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fctimeAll[0:nRamp] + mi*sin(2*pi*fm * timeAll[0:nRamp] + phase))
        snd[nRamp:nRamp+nSamples, 1] = amp* sin(2*pi*fc * timeAll[nRamp:nRamp+nSamples] +mi*sin(2*pi*fm * timeAll[nRamp:nRamp+nSamples] + phase))
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fc * timeAll[nRamp+nSamples:len(timeAll)]+mi*sin(2*pi*fm * timeAll[nRamp+nSamples:len(timeAll)] + phase))
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fctimeAll[0:nRamp] + mi*sin(2*pi*fm * timeAll[0:nRamp] + phase))
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*fc * timeAll[nRamp:nRamp+nSamples] +mi*sin(2*pi*fm * timeAll[nRamp:nRamp+nSamples] + phase))
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fc * timeAll[nRamp+nSamples:len(timeAll)]+mi*sin(2*pi*fm * timeAll[nRamp+nSamples:len(timeAll)] + phase))
    elif channel == "Both":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fctimeAll[0:nRamp] + mi*sin(2*pi*fm * timeAll[0:nRamp] + phase))
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*fc * timeAll[nRamp:nRamp+nSamples] +mi*sin(2*pi*fm * timeAll[nRamp:nRamp+nSamples] + phase))
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*fc * timeAll[nRamp+nSamples:len(timeAll)]+mi*sin(2*pi*fm * timeAll[nRamp+nSamples:len(timeAll)] + phase))
        snd[:, 1] = snd[:, 0]
       

    return snd


def fir2Filt(f1, f2, f3, f4, snd, fs):
    """
    Filter signal with a fir2 filter.

    This function designs and applies a fir2 filter to a sound.
    The frequency response of the ideal filter will transition
    from 0 to 1 between 'f1' and 'f2', and from 1 to zero
    between 'f3' and 'f4'. The frequencies must be given in
    increasing order.

    Parameters
    ----------
    f1 : float
        Frequency in hertz of the point at which the transition
        for the low-frequency cutoff ends. 
    f2 : float
        Frequency in hertz of the point at which the transition
        for the low-frequency cutoff starts.
    f3 : float
        Frequency in hertz of the point at which the transition
        for the high-frequency cutoff starts.
    f4 : float
        Frequency in hertz of the point at which the transition
        for the high-frequency cutoff ends. 
    snd : array of floats
        The sound to be filtered.
    fs : int
        Sampling frequency of 'snd'.

    Returns
    -------
    snd : 2-dimensional array of floats

    Notes
    -------
    If 'f1' and 'f2' are zero the filter will be lowpass.
    If 'f3' and 'f4' are equal to or greater than the nyquist
    frequency (fs/2) the filter will be highpass.
    In the other cases the filter will be bandpass.

    The order of the filter (number of taps) is fixed at 256.
    This function uses internally 'scipy.signal.firwin2'.
       
    Examples
    --------
    >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
    ...     channel='Both', fs=48000, maxLevel=100)
    >>> lpNoise = fir2Filt(f1=0, f2=0, f3=1000, f4=1200, 
    ...     snd=noise, fs=48000) #lowpass filter
    >>> hpNoise = fir2Filt(f1=0, f2=0, f3=24000, f4=26000, 
    ...     snd=noise, fs=48000) #highpass filter
    >>> bpNoise = fir2Filt(f1=400, f2=600, f3=4000, f4=4400, 
    ...     snd=noise, fs=48000) #bandpass filter
    """

    f1 = (f1 * 2) / fs
    f2 = (f2 * 2) / fs
    f3 = (f3 * 2) / fs
    f4 = (f4 * 2) / fs

    n = 256

    if f2 == 0: #low pass
        #print('lowpass')
        f = [0, f3, f4, 1]
        m = [1, 1, 0.00003, 0]
        
    elif f3 < 1: #bandpass
        #print('bandpass')
        f = [0, f1, f2, ((f2+f3)/2), f3, f4, 1]
        m = [0, 0.00003, 1, 1, 1, 0.00003, 0]
        
    else:
        #print('highpass')
        f = [0, f1, f2, 0.999999, 1] #high pass
        m = [0, 0.00003, 1, 1, 0]
        
        
    b = firwin2 (n,f,m);
    x = copy.copy(snd)
    x[:, 0] = convolve(snd[:,0], b, 1)
    x[:, 1] = convolve(snd[:,1], b, 1)
    
    return x

def getRms(sig):
    """
    Compute the root mean square (RMS) value of the signal.

    Parameters
    ----------
    sig : array of floats
        The signal for which the RMS needs to be computed.

    Returns
    -------
    rms : float
       The RMS of 'sig'.

    Examples
    --------
    >>> pt = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> getRms(pt)

    """

    rms = sqrt(mean(sig*sig))
    return rms

def gate(ramps, sig, fs):
    """
    Impose onset and offset ramps to a sound.

    Parameters
    ----------
    ramps : float
        The duration of the ramps.
    sig : array of floats    
        The signal on which the ramps should be imposed.
    fs : int
        The sampling frequency os 'sig'

    Returns
    -------
    sig : array of floats
       The ramped signal.

    Examples
    --------
    >>> noise = broadbandNoise(spectrumLevel=40, duration=200, ramp=0,
    ...     channel='Both', fs=48000, maxLevel=100)
    >>> gate(ramps=10, sig=noise, fs=48000)

    """
    ramps = ramps / 1000.
    nRamp = int(round(ramps * fs))
    timeRamp = arange(0., nRamp)
    nTot = len(sig[:,1])
    nStartSecondRamp = nTot - nRamp
    
    sig[0:nRamp, 0] = sig[0:nRamp, 0] *  ((1-cos(pi * timeRamp/nRamp))/2)
    sig[0:nRamp, 1] = sig[0:nRamp, 1] *  ((1-cos(pi * timeRamp/nRamp))/2)
    sig[nStartSecondRamp:nTot, 0] = sig[nStartSecondRamp:nTot, 0] * ((1+cos(pi * timeRamp/nRamp))/2)
    sig[nStartSecondRamp:nTot, 1] = sig[nStartSecondRamp:nTot, 1] * ((1+cos(pi * timeRamp/nRamp))/2)

    return sig


def glide(freqStart, ftype, excursion, level, duration, phase, ramp, channel, fs, maxLevel):
    """
    Synthetize a rising or falling tone glide with frequency changing
    linearly or exponentially. 


    Parameters
    ----------
    freqStart : float
        Starting frequency in hertz.
    ftype : string
        If 'linear', the frequency will change linearly on a Hz scale.
        If 'exponential', the frequency will change exponentially on a cents scale.
    excursion : float
        If ftype is 'linear', excursion is the total frequency change in Hz.
        The final frequency will be freqStart + excursion.
        If ftype is 'exponential', excursion is the total frequency change in cents.
        The final frequency in Hz will be freqStart*2**(excusrion/1200).
    level : float
        Level of the tone in dB SPL.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       
    Examples
    --------
    >>> gl = glide(freqStart=440, type='exponential', excursion=500,
            level=55, duration=180, phase=0, ramp=10, channel='Both',
            fs=48000, maxLevel=100)

    """

    totDur = duration/1000+ramp/1000*2
    rate = excursion / totDur
    snd = chirp(freqStart, ftype, rate, level, duration, phase, ramp, channel, fs, maxLevel)
    
    return snd

def harmComplFromNarrowbandNoise(F0, lowHarm, highHarm, level, bandwidth, duration, ramp, channel, fs, maxLevel):
    """
    Generate an harmonic complex tone from narrow noise bands.

    Parameters
    ----------
    F0 : float
        Fundamental frequency of the complex.
    lowHarm : int
        Lowest harmonic component number. The first component is #1.
    highHarm : int
        Highest harmonic component number.
    level : float
        The spectrum level of the noise bands in dB SPL.
    bandwidth : float
        The width of each noise band in hertz.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : 'Right', 'Left', 'Both', 'Odd Right' or 'Odd Left'
        Channel in which the tone will be generated. If 'channel'
        if 'Odd Right', odd numbered harmonics will be presented
        to the right channel and even number harmonics to the left
        channel. The opposite is true if 'channel' is 'Odd Left'.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : array of floats

    Examples
    --------
    >>> c1 = harmComplFromNarrowbandNoise(F0=440, lowHarm=3, highHarm=8,
         level=40, bandwidth=80, duration=180, ramp=10, channel='Both',
         fs=48000, maxLevel=100)
    
    """

    sDuration = duration / 1000 #convert from ms to sec
    sRamp = ramp / 1000
    totDur = sDuration + (2 * sRamp)
    nSamples = int(round(sDuration * fs))
    nRamp = int(round(sRamp * fs))
    nTot = nSamples + (nRamp * 2)
    snd = zeros((nTot, 2))
    
    if channel == "Right" or channel == "Left" or channel == "Both":
        tone = zeros((nTot, 2))
    elif channel == "Odd Left" or channel == "Odd Right":
        toneOdd = zeros((nTot, 2))
        toneEven = zeros((nTot, 2))

    for i in range(lowHarm, highHarm+1):
        if channel == "Right" or channel == "Left" or channel == "Both":
            tone =  tone + steepNoise((i*F0) - (bandwidth/2), (i*F0) + (bandwidth/2), level, duration, ramp, channel, fs, maxLevel)
        elif channel == "Odd Left" or channel == "Odd Right":
            if i%2 > 0: #odd harmonic
                        #make the tone in the left channel, then move it where needed
                toneOdd = toneOdd + steepNoise((i*F0) - (bandwidth/2), (i*F0) + (bandwidth/2), level, duration, ramp, "Left", fs, maxLevel)
            else:
                toneEven = toneEven + steepNoise((i*F0) - (bandwidth/2), (i*F0) + (bandwidth/2), level, duration, ramp, "Left", fs, maxLevel)
  

    if channel == "Right" or channel == "Left" or channel == "Both":
        snd = tone
    elif channel == "Odd Left":
        snd[:,0] = toneOdd[:,0]
        snd[:,1] = toneEven[:,0]
    elif channel == "Odd Right":
     snd[:,1] = toneOdd[:,0]
     snd[:,0] = toneEven[:,0]
    
    return snd


def intNCyclesFreq(freq, duration):
    """
    Compute the frequency closest to 'freq' that has an integer number
    of cycles for the given sound duration.

    Parameters
    ----------
    frequency : float
        Frequency in hertz.
    duration : float
        Duration of the sound, in milliseconds.

    Returns
    -------
    adjFreq : float
       
    Examples
    --------
    >>> intNCyclesFreq(freq=2.1, duration=1000)
    2.0
    >>> intNCyclesFreq(freq=2, duration=1000)
    2.0

    """
    
    duration = duration / 1000 #convert from ms to sec
    adjFreq = round(freq*duration)/duration
    return adjFreq

def imposeLevelGlide(sig, deltaL, startTime, endTime, channel, fs):
    """
    Impose a glide in level to a sound.
    
    This function changes the level of a sound with a smooth transition (an amplitude
    ramp) between 'startTime' and 'endTime'. If the signal input to the function
    has a level L, the signal output by the function will have a level L
    between time 0 and 'startTime', and a level L+deltaL between endTime and
    the end of the sound.

    Parameters
    ----------
    sig : float
        Sound on which to impose the level change.
    deltaL : float
        Magnitude of the level change in dB SPL.
    startTime : float
        Start of the level transition in milliseconds.
    endTime : float
        End of the level transition in milliseconds.
    channel : string ('Right', 'Left' or 'Both')
        Channel to which apply the level transition.
    fs : int
        Samplig frequency of the sound in Hz.

    Returns
    -------
    snd : array of floats

    Examples
    --------
    >>> pt = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> pt2 = imposeLevelGlide(sig=pt, deltaL=10, startTime=100,
            endTime=120, channel='Both', fs=48000)
    
    """
    #here we impose an amplitude ramp rather than a linear intensity change
    #give startTime and endTime in ms as arguments, then convert to sec

    if deltaL != 0:

        startTime = startTime / 1000.
        endTime   = endTime   / 1000.

    
        startAmp = 1 #no change
        endAmp = 10**(deltaL/20)
        nSamples = len(sig[:,0])
        startPnt = round(startTime * fs)
        endPnt   = round(endTime   * fs)
        nRamp = endPnt - startPnt
        timeRamp = arange(0., nRamp) 

        x = (startAmp+endAmp)/(startAmp-endAmp)
        y = 2/(startAmp-endAmp)
    
        ramp = ((x+cos(pi * timeRamp/nRamp))/y)
        ampArray = ones(nSamples)
        ampArray[startPnt:endPnt] = ramp
        ampArray[endPnt:len(ampArray)] = repeat(endAmp, len(ampArray[endPnt:len(ampArray)]))

    
        snd = zeros((nSamples,2))
        if channel == "Right":
            snd[:,1] = sig[:,1] * ampArray
        elif channel == "Left":
            snd[:,0] = sig[:,0] * ampArray
        elif channel == "Both":
            snd[:,1] = sig[:,1] * ampArray
            snd[:,0] = sig[:,0] * ampArray

    else:
        snd = sig

    return snd


def itdtoipd(itd, freq):
    """
    Convert an interaural time difference to an equivalent interaural
    phase difference for a given frequency.

    Parameters
    ----------
    itd : float
        Interaural time difference in seconds.
    freq : float
        Frequency in hertz.

    Returns
    -------
    ipd : float

    Examples
    --------
    >>> itd = 300 #microseconds
    >>> itd = 300/1000000 #convert to seconds
    >>> itdtoipd(itd=itd, freq=1000)
    
    """
    
    ipd = (itd / (1.0/freq)) * 2 * pi
    return ipd

def joinSndISI(sndList, ISIList, fs):

    """
    
    Join a list of sounds with given interstimulus intervals

    Parameters
    ----------
    sndList : list of arrays
        The sounds to be joined.
    ISIList : list of floats
        The interstimulus intervals between the sounds in milliseconds.
        This list should have one element less than the sndList.
    fs : int
        Sampling frequency of the sounds in Hz.

    Returns
    -------
    snd : array of floats

    Examples
    --------
    >>> pt1 = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...       ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> pt2 = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...       ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> tone_seq = joinSndISI([pt1, pt2], [500], 48000)
    
    """
    for i in range(len(sndList)):
        if i < len(sndList)-1:
            thisSilence = makeSilence(ISIList[i], fs)
        else:
            thisSilence = makeSilence(0, fs)
        if i == 0:
            snd = sndList[i]
            snd = concatenate((snd, thisSilence), axis=0)
        else:
            snd = concatenate((snd, sndList[i]), axis=0)
            snd = concatenate((snd, thisSilence), axis=0)
    return snd



def makeAsynchChord(freqs, levels, phases, tonesDuration, tonesRamps, tonesChannel, SOA, fs, maxLevel):
    """
    Generate an asynchronous chord.

    This function will add a set of pure tones with a given
    stimulus onset asynchrony (SOA). The temporal order of the
    successive tones is random.

    Parameters
    ----------
    freqs : array or list of floats.
        Frequencies of the chord components in hertz.
    levels : array or list of floats.
        Level of each chord component in dB SPL.
    phases : array or list of floats.
        Starting phase of each chord component.
    tonesDuration : float
        Duration of the tones composing the chord in milliseconds.
        All tones have the same duration.
    tonesRamps : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the tones will be tonesDuration+ramp*2.
    tonesChannel : string ('Right', 'Left' or 'Both')
        Channel in which the tones will be generated.
    SOA : float
        Onset asynchrony between the chord components.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
       
    Examples
    --------
    >>> freqs = [250, 500, 1000]
    >>> levels = [50, 50, 50]
    >>> phases = [0, 0, 0]
    >>> c1 = makeAsynchChord(freqs=freqs, levels=levels, phases=phases,
            tonesDuration=180, tonesRamps=10, tonesChannel='Both',
            SOA=60, fs=48000, maxLevel=100)

    """
     
    seq = numpy.arange(len(freqs))
    numpy.random.shuffle(seq)

    for i in range(len(freqs)):
        thisFreq = freqs[seq[i]]; thisLev = levels[seq[i]]; thisPhase = phases[seq[i]]
        thisTone = pureTone(thisFreq, thisPhase, thisLev, tonesDuration, tonesRamps, tonesChannel, fs, maxLevel)
        if i == 0:
            snd = thisTone
        else:
            snd = addSounds(snd, thisTone, SOA*i, fs)
    return snd

def makeHuggins(F0, lowHarm, highHarm, spectrumLevel, bandwidth, phaseRelationship, noiseType, duration, ramp, fs, maxLevel):
    """
    Synthetise a complex Huggings Pitch.

    Parameters
    ----------
    F0 : float
        The centre frequency of the F0 of the complex in hertz.
    lowHarm : int
        Lowest harmonic component number.
    highHarm : int
        Highest harmonic component number.
    spectrumLevel : float
        The spectrum level of the noise from which
        the complex is derived in dB SPL.
    bandwidth : float
        Bandwidth of the frequency regions in which the
        phase transitions occurr.
    phaseRelationship : string ('NoSpi' or 'NpiSo')
        If NoSpi, the phase of the regions within each frequency band will
        be shifted. If NpiSo, the phase of the regions between each
        frequency band will be shifted.
    noiseType : string ('White' or 'Pink')
        The type of noise used to derive the Huggins Pitch.
    duration : float
        Complex duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).

    Examples
    --------
    >>> hp = makeHuggins(F0=200, lowHarm=1, highHarm=5, spectrumLevel=40,
            bandwidth=65, phaseRelationship='NoSpi', noiseType='White',
            duration=280, ramp=10, fs=48000, maxLevel=100)
    
    """
   
    sDuration = duration / 1000 #convert from ms to sec
    sRamp = ramp / 1000
    totDur = sDuration + (2 * sRamp)
    nSamples = int(round(sDuration * fs))
    nRamp = int(round(sRamp * fs))
    nTot = nSamples + (nRamp * 2)
    snd = zeros((nTot, 2))

    tone = broadbandNoise(spectrumLevel, duration+(ramp*2), 0, "Both", fs, maxLevel)
    if noiseType == "Pink":
        makePink(tone, fs)
    for i in range(lowHarm, highHarm+1):
        if phaseRelationship == "NoSpi":
            #print("NoSpi")
            tone = phaseShift(tone, ((i*F0) - (bandwidth/2)), ((i*F0) + (bandwidth/2)), pi, "Left", fs)
        elif phaseRelationship == "NpiSo":
            #print("NpiSo")
            if i == lowHarm:
                tone = phaseShift(tone, 10, (i*F0) - (bandwidth/2), pi, "Left", fs)
            elif i == highHarm + 1:
                tone = phaseShift(tone, ((i-1)*F0) + (bandwidth/2), (i*F0) - (bandwidth/2), pi, "Left", fs)
                tone = phaseShift(tone, (i*F0) + (bandwidth/2), fs/2, pi, "Left", fs)
            else:
                tone = phaseShift(tone, ((i-1)*F0) + (bandwidth/2), (i*F0) - (bandwidth/2), pi, "Left", fs)
    
    tone = gate(ramp, tone, fs)    
    snd = tone

    return snd

def makePink(sig, fs):
    """
    Convert a white noise into a pink noise.

    The spectrum level of the pink noise at 1000 Hz will be equal to
    the spectrum level of the white noise input to the function.

    Parameters
    ----------
    sig : array of floats
        The white noise to be turned into a pink noise.
    fs : int
        Sampling frequency of the sound.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).

    Examples
    --------
     >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
     ...     channel='Both', fs=48000, maxLevel=100)
     >>> noise = makePink(sig=noise, fs=48000)
    
    """
    nSamples = len(sig[:,0])
    if nSamples < 2:
        pass
    else:
        ref = 1 + (1000 * nSamples/fs)
        x = rfft(sig[:,0], nSamples)
        idx = arange(1, len(x))
        mag = zeros(len(x))
        mag[1:len(x)] = abs(x[1:len(x)]) * sqrt(ref/idx)
        mag[0] = abs(x[0])
        ph = angle(x)
        x = mag * (cos(ph) + 1j * sin(ph))
    
        sig0 = irfft(x, nSamples)


        x = rfft(sig[:,1], nSamples)
        idx = arange(1, len(x))
        mag = zeros(len(x))
        mag[1:len(x)] = abs(x[1:len(x)]) * sqrt(ref/idx)
        mag[0] = abs(x[0])
        ph = angle(x)
        x = mag * (cos(ph) + 1j * sin(ph))

        sig1 = irfft(x, nSamples)

        sig[:, 0] = sig0
        sig[:, 1] = sig1
    
    return sig



def makePinkRef(sig, fs, refHz):
    """
    Convert a white noise into a pink noise.

    The spectrum level of the pink noise at the frequency 'refHz'
    will be equal to the spectrum level of the white noise input
    to the function.

    Parameters
    ----------
    sig : array of floats
        The white noise to be turned into a pink noise.
    fs : int
        Sampling frequency of the sound.
    refHz : int
        Reference frequency in Hz. The amplitude of the other
        frequencies will be scaled with respect to the amplitude
        of this frequency.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).

    Examples
    --------
     >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
     ...     channel='Both', fs=48000, maxLevel=100)
     >>> noise = makePink(sig=noise, fs=48000, refHz=1000)
    
    """
    
    nSamples = len(sig[:,0])
    ref = 1 + (refHz * nSamples/fs)

    x = rfft(sig[:,0])
    idx = arange(1, len(x))
    mag = zeros(len(x))
    mag[1:len(x)] = abs(x[1:len(x)]) * sqrt(ref/idx)
    mag[0] = abs(x[0])
    ph = angle(x)
    x = mag * (cos(ph) + 1j * sin(ph))
    
    sig0 = irfft(x)


    x = rfft(sig[:,1])
    idx = arange(1, len(x))
    mag = zeros(len(x))
    mag[1:len(x)] = abs(x[1:len(x)]) * sqrt(ref/idx)
    mag[0] = abs(x[0])
    ph = angle(x)
    x = mag * (cos(ph) + 1j * sin(ph))

    sig1 = irfft(x)

    sig[:, 0] = sig0
    sig[:, 1] = sig1
    
    return sig


def makeSilence(duration, fs):
    """
    Generate a silence.

    This function just fills an array with zeros for the
    desired duration.
    
    Parameters
    ----------
    duration : float
        Duration of the silence in milliseconds.
    fs : int
        Samplig frequency in Hz.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       

    Examples
    --------
    >>> sil = makeSilence(duration=200, fs=48000)

    """
    #duration in ms
    duration = duration / 1000 #convert from ms to sec
    nSamples = int(round(duration * fs))
    snd = zeros((nSamples, 2))
    
    return snd

def makeSimpleDichotic(F0, lowHarm, highHarm, cmpLevel, lowFreq, highFreq, spacing, sigBandwidth, phaseRelationship, dichoticDifference, itd, ipd, narrowBandCmpLevel, duration, ramp, fs, maxLevel):
    """
    Generate harmonically related dichotic pitches, or equivalent
    harmonically related narrowband tones in noise.

    This function generates first a pink noise by adding closely spaced
    sinusoids in a wide frequency range. Then, it can apply an interaural
    time difference (ITD), an interaural phase difference (IPD) or a
    level increase to harmonically related narrow frequency bands
    within the noise. In the first two cases (ITD and IPD) the result
    is a dichotic pitch. In the last case the pitch can also be heard
    monaurally; adjusting the level increase its salience can be closely
    matched to that of a dichotic pitch.
    
    Parameters
    ----------
    F0 : float
        Centre frequency of the fundamental in hertz.
    lowHarm : int
        Lowest harmonic component number.
    highHarm : int
        Highest harmonic component number.
    cmpLevel : float
        Level of each sinusoidal frequency component of the noise.
    lowFreq : float
        Lowest frequency in hertz of the noise.
    highFreq : float
        Highest frequency in hertz of the noise.
    spacing : float
        Spacing in cents between the sinusoidal components used to generate the
        noise.
    sigBandwidth : float
        Width in cents of each harmonically related frequency band.
    phaseRelationship : string ('NoSpi' or 'NpiSo')
        If NoSpi, the phase of the regions within each frequency band will
        be shifted. If NpiSo, the phase of the regions between each
        frequency band will be shifted.
    dichoticDifference : string (one of 'IPD', 'ITD', 'Level')
        The manipulation to apply to the heramonically related
        frequency bands. 
    itd : float
        Interaural time difference in microseconds to apply
        to the harmonically related frequency bands. Applied
        only if 'dichoticDifference' is 'ITD'.
    ipd : float
        Interaural phase difference in radians to apply
        to the harmonically related frequency bands. Applied
        only if 'dichoticDifference' is 'IPD'.
    narrowBandCmpLevel : float
        Level of the sinusoidal components in the frequency bands.
        If the 'narrowBandCmpLevel' is greater than the level
        of the background noise ('cmpLevel'), a complex tone
        consisting of narrowband noises in noise will be generated.
    duration : float
        Sound duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       

    Examples
    --------
    >>> s1 = makeSimpleDichotic(F0=250, lowHarm=1, highHarm=3, cmpLevel=30,
        lowFreq=40, highFreq=1200, spacing=10, sigBandwidth=100,
        phaseRelationship='NoSpi', dichoticDifference='IPD', itd=0,
        ipd=3.14, narrowBandCmpLevel=0, duration=280, ramp=10,
        fs=48000, maxLevel=100)

    """""" 

    Keyword arguments:
    F0 -- Fundamental frequency (Hz)
    lowHarm -- Number of the lowest harmonic
    highHarm -- Number of the highest harmonic
    cmpLevel -- level in dB SPL of each sinusoid that makes up the noise
    lowCmp -- lowest frequency (Hz)
    highCmp -- highest frequency (Hz)
    spacing -- spacing between frequency components (Cents)
    sigBandwidth -- bandwidth of each harmonic band (Cents)
    phaseRelationship -- NoSpi or NpiSo
    dichotic difference -- IPD, ITD or Level
    itd -- interaural time difference microseconds
    ipd -- interaural phase difference in radians
    narrowBandCmpLevel - level of frequency components in the harmonic bands (valid only if dichotic difference is Level)
    duration -- duration (excluding ramps) in ms
    ramp -- ramp duration in ms
    fs -- sampling frequency
    maxLevel --
    
    """
    
    sDuration = duration/1000 #convert from ms to sec
    sRamp = ramp/1000

    totDur = sDuration + (2 * sRamp)
    nSamples = int(round(sDuration * fs))
    nRamp = int(round(sRamp * fs))
    nTot = nSamples + (nRamp * 2)
    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 
    snd = zeros((nTot, 2))
    noisBandwidth = 1200*log2(highFreq/lowFreq) #in cents
    nComponents = int(floor(noisBandwidth/spacing))
    
    amp = 10**((cmpLevel - maxLevel) / 20)
    freqs = zeros(nComponents)
    freqs[0] = lowFreq
    for i in range(1, nComponents): #indexing starts from 1
        freqs[i] = freqs[i-1]*(2**(spacing/1200))

    phasesR = numpy.random.uniform(0, 2*pi, nComponents)
    sinArray = zeros((nComponents, nTot))

    for i in range(0, nComponents):
        sinArray[i,] = amp* sin(2*pi*freqs[i] * timeAll + phasesR[i])
    freqsToShift = []
    nCompsXBand = []
    for i in range(lowHarm, highHarm+1):
        thisFreq = F0*i;
        prevFreq = F0*(i-1)
        lo = thisFreq*2**(-(sigBandwidth/2)/1200)
        hi = thisFreq*2**((sigBandwidth/2)/1200)
        hiPrev = prevFreq*2**((sigBandwidth/2)/1200)
        if phaseRelationship == "NoSpi":
            thisFreqsToShift = numpy.where((freqs>lo) & (freqs<hi))
            freqsToShift = numpy.append(freqsToShift, thisFreqsToShift)
        elif phaseRelationship == "NpiSo":
            if i == 0:
                thisFreqsToShift = numpy.where((freqs>lowFreq) & (freqs<lo))
            else:
                thisFreqsToShift = numpy.where((freqs>hiPrev) & (freqs<lo))
            if i == highHarm:
                foo = numpy.where(freqs>hi)
                thisFreqsToShift = numpy.append(thisFreqsToShift, foo)
            freqsToShift = numpy.append(freqsToShift, thisFreqsToShift)
                
                
    sinArrayLeft = copy.copy(sinArray)
   
    if dichoticDifference == "IPD":
        for i in range(0,len(freqsToShift)):
            sinArrayLeft[freqsToShift[i],] =  amp* sin(2*pi*freqs[freqsToShift[i]] * timeAll + (phasesR[freqsToShift[i]]+ipd))
    elif dichoticDifference == "ITD":
        for i in range(0,len(freqsToShift)):
            thisIpd = itdtoipd(itd/1000000., freqs[freqsToShift[i]])
            sinArrayLeft[freqsToShift[i],] =  amp* sin(2*pi*freqs[freqsToShift[i]] * timeAll + (phasesR[freqsToShift[i]]+thisIpd))
    elif dichoticDifference == "Level":
        amp2 = 10**((narrowBandCmpLevel - maxLevel) / 20);
        for i in range(0,len(freqsToShift)):
            sinArrayLeft[freqsToShift[i],]  = amp2* sin(2*pi*freqs[freqsToShift[i]] * timeAll + phasesR[freqsToShift[i]])
        # raise the levels of the narrow band in both the right and left ears
        sinArray = sinArrayLeft
    snd[:,0] = sum(sinArray,0)
    snd[:,1] = sum(sinArrayLeft,0)
    snd = gate(ramp, snd, fs)
    return snd


## def makeToneSequenceWithJitter(nTones, tonesFreq, tonesLevel, tonesDuration, tonesRamps, tonesChannel, ISI, jitter, fs, maxLevel):
##     """
##     Sum a set of pure tones with a jittered onset.

##     Parameters
##     ----------
##     nTones : int
        
##     Returns
##     ----------

    
##     """
##     tonesTotalDuration = tonesDuration + tonesRamps*2
##     soundSequenceDuration = jitter*2 + tonesTotalDuration*nTones + ISI*(nTones-1)
##     soundSequence = makeSilence(soundSequenceDuration, fs)
##     thisTone = pureTone(tonesFreq, 0, tonesLevel, tonesDuration, tonesRamps, tonesChannel, fs, maxLevel)
##     toneOnsets = numpy.zeros(nTones)
##     for i in range(nTones):
##         toneOnsets[i] = jitter + i*(tonesTotalDuration+ISI)
##     toneOnsets = toneOnsets + numpy.random.uniform(-jitter, jitter, nTones)
##     for i in range(nTones):
##         soundSequence = addSounds(soundSequence, thisTone, toneOnsets[i], fs)

##     return soundSequence


def nextpow2(x):
    """
    Next power of two.

    Parameters
    ----------
    x : int
        Base number.

    Returns
    -------
    out : float
        The power to which 2 should be raised.

    Examples
    --------
    >>> nextpow2(511)
    9
    >>> 2**9
    512
    
    """
    out = int(ceil(log2(x)))
    return out
#def nextpow2(i):
#    n = 2
#    while n < i:
#        n = n * 2
#    return n



def phaseShift(sig, f1, f2, phase_shift, channel, fs):
    """
    Shift the phases of a sound within a given frequency region.

    Parameters
    ----------
    sig : array of floats
        Input signal.
    f1 : float
        The start point of the frequency region to be
        phase-shifted in hertz.
    f2 : float
        The end point of the frequency region to be
        phase-shifted in hertz.
    phase_shift : float
        The amount of phase shift in radians.
    channel : string (one of 'Right', 'Left' or 'Both')
        The channel in which to apply the phase shift.
    fs : float
        The sampling frequency of the sound.
        
    Returns
    -------
    out : 2-dimensional array of floats

    Examples
    --------
    >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
    ...     channel='Both', fs=48000, maxLevel=100)
    >>> hp = phaseShift(sig=noise, f1=500, f2=600, phase_shift=3.14,
            channel='Left', fs=48000) #this generates a Dichotic Pitch
    
    """
    
    nSamples = len(sig[:,0])
    fftPoints = 2**nextpow2(nSamples)

    #in Matlab 1+ to skip DC component, but python indexing starts from 0
    start1 =  round(f1 * fftPoints / fs)
    end1   =  round(f2 * fftPoints / fs)
    # symmetric points, for Matlab need to add 2 to skip DC component and because start1 subtracts one point more
    start2 = fftPoints - start1
    end2 = fftPoints - end1
    snd = zeros((nSamples, 2))

    if channel == "Left":
        x = fft(sig[:,0], fftPoints)
        pnts = int_(arange(start1, end1+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) + phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        pnts = int_(arange(end2, start2+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) - phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        x = real(ifft(x))
        snd[:,0] = x[arange(0, nSamples, 1)]
        snd[:,1] = sig[:,1]
    elif channel == "Right":
        x = fft(sig[:,1], fftPoints)
        pnts = int_(arange(start1, end1+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) + phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        pnts = int_(arange(end2, start2+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) - phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        x = real(ifft(x))
        snd[:,1] = x[arange(0, nSamples, 1)]
        snd[:,0] = sig[:,0]
    elif channel == "Both":
        x = fft(sig[:,0], fftPoints)
        pnts = int_(arange(start1, end1+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) + phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        pnts = int_(arange(end2, start2+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) - phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        x = real(ifft(x))
        snd[:,0] = x[arange(0, nSamples, 1)]

        x = fft(sig[:,1], fftPoints)
        pnts = int_(arange(start1, end1+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) + phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        pnts = int_(arange(end2, start2+1, 1))
        mag = abs(x[pnts])
        newPhase = angle(pnts) - phase_shift
        x[pnts] = mag * (cos(newPhase) + (1j * sin(newPhase)))

        x = real(ifft(x))
        snd[:,1] = x[arange(0, nSamples, 1)]

    return snd


def pinkNoiseFromSin(compLevel, lowCmp, highCmp, spacing, duration, ramp, channel, fs, maxLevel):
    """
    Generate a pink noise by adding sinusoids spaced by a fixed
    interval in cents.

    Parameters
    ----------
    compLevel : float
        Level of each sinusoidal component in dB SPL.
    lowCmp : float
        Frequency of the lowest noise component in hertz.
    highCmp : float
        Frequency of the highest noise component in hertz.
    spacing : float
        Spacing between the frequencies of the sinusoidal components
        in hertz.
    duration : float
        Noise duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the noise will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
        
    Examples
    --------
    >>> noise = pinkNoiseFromSin(compLevel=23, lowCmp=100, highCmp=1000,
        spacing=20, duration=180, ramp=10, channel='Both',
        fs=48000, maxLevel=100)
    
    """

    sDuration = duration / 1000 #convert from ms to sec
    sRamp = ramp / 1000

    totDur = sDuration + (2 * sRamp)
    nSamples = int(round(sDuration * fs))
    nRamp = int(round(sRamp * fs))
    nTot = nSamples + (nRamp * 2)
    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 
    snd = zeros((nTot, 2))
    noisBandwidth = 1200*log2(highCmp/lowCmp) #in cents
    nComponents = int(floor(noisBandwidth/spacing))
    amp = 10**((compLevel - maxLevel) / 20)
    freqs = zeros(nComponents)
    freqs[0] = lowCmp
    for i in range(1, nComponents): #indexing starts from 1
        freqs[i] = freqs[i-1]*(2**(spacing/1200.))

    phasesR = numpy.random.uniform(0, 2*pi, nComponents)
    sinArray = zeros((nComponents, nTot))

    for i in range(0, nComponents):
        sinArray[i,] = amp* sin(2*pi*freqs[i] * timeAll + phasesR[i])
    
    if channel == "Right":
        snd[:,1] = sum(sinArray,0)
    elif channel == "Left":
        snd[:,0] = sum(sinArray,0)
    elif channel == "Both":
        snd[:,1] = sum(sinArray,0)
        snd[:,0] = snd[:,1]
    snd = gate(ramp, snd, fs)    
    return snd


def pinkNoiseFromSin2(compLevel, lowCmp, highCmp, spacing, duration, ramp, channel, fs, maxLevel):
    """
    Generate a pink noise by adding sinusoids spaced by a fixed
    interval in cents.

    This function should produce the same output of pinkNoiseFromSin,
    it simply uses a different algorithm that uses matrix operations
    instead of a for loop. It doesn't seem to be much faster though.

    Parameters
    ----------
    compLevel : float
        Level of each sinusoidal component in dB SPL.
    lowCmp : float
        Frequency of the lowest noise component in hertz.
    highCmp : float
        Frequency of the highest noise component in hertz.
    spacing : float
        Spacing between the frequencies of the sinusoidal components
        in hertz.
    duration : float
        Noise duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the noise will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
        
    Examples
    --------
    >>> noise = pinkNoiseFromSin2(compLevel=23, lowCmp=100, highCmp=1000,
        spacing=20, duration=180, ramp=10, channel='Both',
        fs=48000, maxLevel=100)
    
    """

    sDuration = duration / 1000 #convert from ms to sec
    sRamp = ramp / 1000

    totDur = sDuration + (2 * sRamp)
    nSamples = int(round(sDuration * fs))
    nRamp = int(round(sRamp * fs))
    nTot = nSamples + (nRamp * 2)
    timeAll = arange(0, nTot) / fs
    snd = zeros((nTot, 2))
    noisBandwidth = 1200*log2(highCmp/lowCmp) #in cents
    nComponents = int(floor(noisBandwidth/spacing))
    amp = 10**((compLevel - maxLevel) / 20)
    freqs = zeros((nComponents,1))
    freqs[0] = lowCmp
    for i in range(1, nComponents): #indexing starts from 1
        freqs[i] = freqs[i-1]*(2**(spacing/1200.))
    #freqs = freqs.reshape(nComponents,1)
    phasesR = numpy.random.uniform(0, 2*pi, (nComponents,1))
    #phasesR = phasesR.reshape(nComponents,1)
    sinMatrix = zeros((nComponents, nTot))
    timeMatrix = zeros((nComponents, nTot))
    timeMatrix[:] = timeAll

    #for i in range(0, nComponents):
    #    sinMatrix[i,] = amp* sin(2*pi*freqs[i] * timeAll + phasesR[i])

    sinMatrix = amp*sin(2*pi*freqs*timeMatrix+phasesR)
    
    if channel == "Right":
        snd[:,1] = sum(sinMatrix,0)
    elif channel == "Left":
        snd[:,0] = sum(sinMatrix,0)
    elif channel == "Both":
        snd[:,1] = sum(sinMatrix,0)
        snd[:,0] = snd[:,1]
    snd = gate(ramp, snd, fs)    
    return snd


def pureTone(frequency, phase, level, duration, ramp, channel, fs, maxLevel):
    """
    Synthetise a pure tone.

    Parameters
    ----------
    frequency : float
        Tone frequency in hertz.
    phase : float
        Starting phase in radians.
    level : float
        Tone level in dB SPL.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       

    Examples
    --------
    >>> pt = pureTone(frequency=440, phase=0, level=65, duration=180,
    ...     ramp=10, channel='Right', fs=48000, maxLevel=100)
    >>> pt.shape
    (9600, 2)
    
    """

    if channel not in ["Right", "Left", "Both"]:
        raise TypeError("Invalid channel argument. Channel must be one of 'Right', 'Left' or 'Both'")
    
    amp = 10**((level - maxLevel) / 20.)
    duration = duration / 1000 #convert from ms to sec
    ramp = ramp / 1000

    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp) 

    snd = zeros((nTot, 2))
    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 1] = amp* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
    elif channel == "Both":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[0:nRamp] + phase)
        snd[nRamp:nRamp+nSamples, 0] = amp* sin(2*pi*frequency * timeAll[nRamp:nRamp+nSamples] + phase)
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * sin(2*pi*frequency * timeAll[nRamp+nSamples:len(timeAll)] + phase)
        snd[:, 1] = snd[:, 0]
       

    return snd

def scale(level, sig):
    """
    Increase or decrease the amplitude of a sound signal.

    Parameters
    ----------
    level : float
        Desired increment or decrement in dB SPL.
    signal : array of floats
        Signal to scale.

    Returns
    -------
    sig : 2-dimensional array of floats
       
    Examples
    --------
    >>> noise = broadbandNoise(spectrumLevel=40, duration=180, ramp=10,
    ...     channel='Both', fs=48000, maxLevel=100)
    >>> noise = scale(level=-10, sig=noise) #reduce level by 10 dB

    """
    #10**(level/20) is the amplitude corresponding to level
    #by multiplying the amplitudes we're adding the decibels
    # 20*log10(a1*a2) = 20*log10(a1) + 20*log10(a2)
    sig = sig * 10**(level/20)
    return sig


def steepNoise(frequency1, frequency2, level, duration, ramp, channel, fs, maxLevel):
    """
    Synthetise band-limited noise from the addition of random-phase
    sinusoids.

    Parameters
    ----------
    frequency1 : float
        Start frequency of the noise.
    frequency2 : float
        End frequency of the noise.
    level : float
        Noise spectrum level.
    duration : float
        Tone duration (excluding ramps) in milliseconds.
    ramp : float
        Duration of the onset and offset ramps in milliseconds.
        The total duration of the sound will be duration+ramp*2.
    channel : string ('Right', 'Left' or 'Both')
        Channel in which the tone will be generated.
    fs : int
        Samplig frequency in Hz.
    maxLevel : float
        Level in dB SPL output by the soundcard for a sinusoid of amplitude 1.

    Returns
    -------
    snd : 2-dimensional array of floats
        The array has dimensions (nSamples, 2).
       
    Examples
    --------
    >>> nbNoise = steepNoise(frequency=440, frequency2=660, level=65,
    ...     duration=180, ramp=10, channel='Right', fs=48000, maxLevel=100)
    
    """

    duration = duration/1000 #convert from ms to sec
    ramp = ramp/1000

    totDur = duration + (2 * ramp)
    nSamples = int(round(duration * fs))
    nRamp = int(round(ramp * fs))
    nTot = nSamples + (nRamp * 2)

    spacing = 1 / totDur
    components = 1 + floor((frequency2 - frequency1) / spacing)
    # SL = 10*log10(A^2/NHz) 
    # SL/10 = log10(A^2/NHz)
    # 10^(SL/10) = A^2/NHz
    # A^2 = 10^(SL/10) * NHz
    # RMS = 10^(SL/20) * sqrt(NHz) where NHz is the spacing between harmonics
    amp =  10**((level - maxLevel) / 20.) * sqrt((frequency2 - frequency1) / components)
    
    timeAll = arange(0, nTot) / fs
    timeRamp = arange(0, nRamp)
    snd = zeros((nTot, 2))

    noise= zeros(nTot)
    for f in arange(frequency1, frequency2+spacing, spacing):
        radFreq = 2 * pi * f 
        phase = numpy.random.random(1) * 2 * pi
        noise = noise + sin(phase + (radFreq * timeAll))

    if channel == "Right":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1] = amp * noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * noise[nRamp+nSamples:len(timeAll)]
    elif channel == "Left":
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0] = amp * noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * noise[nRamp+nSamples:len(timeAll)]
    elif channel == "Both":
        snd[0:nRamp, 1] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 1] = amp * noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 1] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * noise[nRamp+nSamples:len(timeAll)]
        snd[0:nRamp, 0] = amp * ((1-cos(pi * timeRamp/nRamp))/2) * noise[0:nRamp]
        snd[nRamp:nRamp+nSamples, 0] = amp * noise[nRamp:nRamp+nSamples]
        snd[nRamp+nSamples:len(timeAll), 0] = amp * ((1+cos(pi * timeRamp/nRamp))/2) * noise[nRamp+nSamples:len(timeAll)]

    return snd

 
   





