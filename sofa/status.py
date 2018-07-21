"""a fancy status class"""


class Status(tuple):
    _attrs = []
    _dashboard_fmt = []

    def __new__(cls, **kwargs):
        args = []
        for attr in cls._attrs:
            if attr not in kwargs:
                raise TypeError(attr)
            args.append(kwargs[attr])
        return super(Status, cls).__new__(cls, args)

    @property
    def dashboard(self):
        return self._render(self._dashboard_fmt, 'dashboard')

    def __repr__(self):
        rendered = []
        for status in self:
            rendered.append(str(status))
        return self.__class__.__name__ + '(' + ', '.join(rendered) + ')'

    def _render(self, fmt, preferred_child_attr):
        if not fmt:
            return str(self)
        attrs = {}
        i = 0
        for attr in self._attrs:
            try:
                attrs[attr] = getattr(self[i], preferred_child_attr)
            except AttributeError:
                attrs[attr] = self[i]
            except TypeError:
                attrs[attr] = self[i]
            i += 1
        args = [self]
        try:
            return " ".join(fmt).format(*args, **attrs)
        except AttributeError as exc:
            raise RuntimeError(exc)

    def __getattr__(self, attr):
        i = 0
        for defined_attr in self._attrs:
            if attr == defined_attr:
                return self[i]
            i += 1
        raise AttributeError("%s not found in %s" % (attr, self))

    def __dict__(self):
        return self.as_dict

    @property
    def as_dict(self):
        i = 0
        status = {}
        for attr in self._attrs:
            try:
                status[attr] = self[i].__dict__()
            except AttributeError:
                status[attr] = self[i]
            except TypeError:
                status[attr] = self[i]
            i += 1
        return status

    @property
    def attrs(self):
        return self._attrs
