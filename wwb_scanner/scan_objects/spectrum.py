from wwb_scanner.scan_objects import Sample

class Spectrum(object):
    def __init__(self, **kwargs):
        self.step_size = kwargs.get('step_size')
        self.samples = {}
        samples = kwargs.get('samples', {})
        if isinstance(samples, dict):
            for frequency, magnitude in samples.items():
                self.add_sample(frequency=frequency, magnitude=magnitude)
        else:
            for sample_kwargs in samples:
                self.add_sample(**sample_kwargs)
    def add_sample(self, **kwargs):
        if kwargs.get('frequency') in self.samples:
            sample = self.samples[kwargs['frequency']]
            sample.magnitude = kwargs.get('magnitude')
            return sample
        kwargs.setdefault('spectrum', self)
        sample = Sample(**kwargs)
        self.samples[sample.frequency] = sample
        return sample
    def iter_frequencies(self):
        for key in sorted(self.samples.keys()):
            yield key
    def iter_samples(self):
        for key in self.iter_frequencies():
            yield self.samples[key]
        
