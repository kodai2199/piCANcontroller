from django.db import models


# Create your models here.
class Installation(models.Model):
    """
    This class defines a model for an Installation.

    Questa classe definisce un modello per un Impianto.
    """

    """
    Fields
    """
    installation_code = models.CharField(help_text='CPx Code', max_length=255, default="default")
    imei = models.CharField(unique=True, help_text="IMEI Code", max_length=255)
    online = models.BooleanField(help_text="Online state", default=False)
    inlet_pressure = models.IntegerField(help_text="Inlet pressure (Bar)", null=True, blank=True, default=0)
    inlet_temperature = models.IntegerField(help_text="Inlet temperature (°C)", null=True, blank=True, default=0)
    outlet_pressure = models.IntegerField(help_text="Outlet pressure (Bar)", null=True, blank=True, default=0)
    working_hours_counter = models.IntegerField(help_text="Total working hours", null=True, blank=True, default=0)
    working_minutes_counter = models.IntegerField(help_text="Working minutes", null=True, blank=True, default=0)
    anti_drip = models.BooleanField(help_text="Anti-drip", default=False)
    time_limit = models.BooleanField(help_text="Daily time limit reached", default=False)
    start_code = models.CharField(help_text="Start code", null=True, blank=True, max_length=255, default="0x0000")
    alarm = models.BooleanField(help_text="Alarm state", default=False)

    # Meaning not yet sure...
    bk_service = models.BooleanField(help_text="Backup service", default=False)
    tl_service = models.BooleanField(help_text="Time limit service", default=False)
    rb_service = models.BooleanField(help_text="RB service", default=False)

    run = models.BooleanField(help_text="Running state", default=False)

    """
    Metadata
    Permissions, ...
    """
    class Meta:
        permissions = (("can_see_advanced_info", "Can see advanced informations"), )

    """
    Methods
    """
    def __str__(self):
        # A human-readable form of an Installation model
        # TODO: implement more informations
        return self.imei


class Command(models.Model):
    """
    This class defines a model for a Command. A Command
    is a command string, each with its recipient's IMEI.
    Commands are sent by views, after specific requests. (e.g. RUN)

    Questa classe definisce un modello per un Comando.
    Un Comando è una stringa di comando, ciacuno associato
    all'IMEI del destinatario. I comandi sono inviati tramite
    l'interfaccia web, in seguito a specifiche richieste (es. RUN)
    """

    """
    Fields
    """
    # A single command can be sent to an IMEI at one time
    imei = models.CharField(help_text="Recipient's IMEI", unique=True, max_length=255)
    command_string = models.CharField(help_text="Command string", max_length=255)

    def __str__(self):
        # A human-readable form of a Command model
        info = "For {}: {}".format(self.imei, self.command_string)
        return info
