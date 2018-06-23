/******************************************************************************
 *
 * Python wrapper for reading/writing TigerJet registers.  This is derived from
 * Môshe van der Sterre's tjapi.c Source here: http://www.moshe.nl/tjapi.html
 *
 * These modifications were done with Môshe van der Sterre's permission.
 *
 *****************************************************************************/
#include <Python.h>
#include <unistd.h>
#include <limits.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <asm/types.h>
#include <linux/hiddev.h>

#define TIGERJET_VENDOR_ID 0x06E6

static PyObject *pytjapi_write(PyObject *self, PyObject *args);
static PyObject *pytjapi_read(PyObject *self, PyObject *args);
static PyObject *pytjapi_is_tigerjet(PyObject *self, PyObject *args);

static char module_docstring[] =
  "Python wrapper for reading/writing TigerJet registers";

static char read_docstring[] =
   "read(hid_fd, register_addr)\n\nreturns data register_addr";

static char write_docstring[] =
  "write(hid_fd, register_addr, data)\n\nreturns None";

static char tj_docstring[] =
  "is_tigerjet(hid_fd)\n\nreturns Boolean";

static PyMethodDef module_methods[] = {
	{"read", pytjapi_read, METH_VARARGS, read_docstring},
	{"write", pytjapi_write, METH_VARARGS, write_docstring},
	{"is_tigerjet", pytjapi_is_tigerjet, METH_VARARGS, tj_docstring},
	{NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "pytjapi",       
    module_docstring,
    -1,
    module_methods
};
#endif

int is_tigerjet(int hid_fd, int *pid)
{
    struct hiddev_devinfo devinfo;
    int ret = 0;

    memset(&devinfo, 0, sizeof(devinfo));
    ret = ioctl(hid_fd, HIDIOCGDEVINFO, &devinfo);
    if (ret != 0) {
        return (-1);
    }

    if (devinfo.vendor != TIGERJET_VENDOR_ID) {
        return (0);
    }

    if (pid) {
	   memcpy(pid, &devinfo.product, sizeof(devinfo.product));
    }

    return (1);
}

static int read_write_tigerjet(int hid_fd,
			       unsigned char reg_addr,
			       unsigned char *write_data,
			       unsigned char *read_data)
{
    struct hiddev_report_info report_info;
    struct hiddev_usage_ref_multi uref_multi;
    unsigned char w_reg_addr = 0;
    unsigned char r_reg_addr = 0;
    unsigned char data = 0;
    unsigned char data_len = 0;
    int ret = 0;

    if (!is_tigerjet(hid_fd, NULL)) {
	return (-1);
    }

    /* Can only read or write, in one call */
    if (!read_data == !write_data) {
	return (-1);
    }

    memset(&report_info, 0, sizeof(struct hiddev_report_info));
    memset(&uref_multi, 0, sizeof(struct hiddev_usage_ref_multi));

    report_info.report_type = 3;
    report_info.report_id = 256;

    uref_multi.uref.report_type = 3;
    uref_multi.uref.report_id = 256;
    uref_multi.uref.field_index = 0;
    uref_multi.uref.usage_index = 0;

    if (write_data) {
	/* Write a register */
	w_reg_addr = reg_addr;
	data = *write_data;
	data_len = 1;
	uref_multi.num_values = 5;
    } else {
        /* Read a register */
        *read_data = 0;
        r_reg_addr = reg_addr;
	uref_multi.num_values = 4;
    }

    uref_multi.values[0] = 2;
    uref_multi.values[1] = w_reg_addr; /* Write address */
    uref_multi.values[2] = r_reg_addr; /* Read address */
    uref_multi.values[3] = data_len;   /* Data length for write*/
    uref_multi.values[4] = data;       /* Data for write */

    ret = ioctl(hid_fd, HIDIOCSUSAGES, &uref_multi);
    if (ret != 0) {
		return (errno);
    }

    ret = ioctl(hid_fd, HIDIOCSREPORT, &report_info);
    if (ret != 0) {
		return (errno);
    }

    usleep(5);

    /* Query Tigerjet again to get the data for the read address */
    if (read_data) {
		ret = ioctl(hid_fd, HIDIOCGREPORT, &report_info);
		if (ret != 0){
			return (errno);
		}

		uref_multi.num_values = 1;
		ret = ioctl(hid_fd, HIDIOCGUSAGES, &uref_multi);
		if (ret != 0) {
			return (errno);
		}

		*read_data = uref_multi.values[0];
    }

    return (0);
}

int write_tigerjet(int hid_fd, unsigned char reg_addr, unsigned char data)
{
    unsigned char write_data = data;
    return read_write_tigerjet(hid_fd, reg_addr, &write_data, NULL);
}

int read_tigerjet(int hid_fd, unsigned char reg_addr, unsigned char *read_data)
{
    return read_write_tigerjet(hid_fd, reg_addr, NULL, read_data);
}

static PyObject *pytjapi_write(PyObject *self, PyObject *args)
{
    int hid_fd = 0;
	int ret = 0;
    unsigned char reg_addr;
	unsigned char write_data;

    if (!PyArg_ParseTuple(args, "ibb", &hid_fd, &reg_addr, &write_data)) {
		PyErr_SetString(PyExc_RuntimeError, "Error parsing parameters");
		return (NULL);
	}

    ret = read_write_tigerjet(hid_fd, reg_addr, &write_data, NULL);
	if (ret != 0) {
		PyErr_SetString(PyExc_RuntimeError, "Error Writing TigerJet Register");
        return (NULL);
	}

	return (Py_BuildValue(""));
}

static PyObject *pytjapi_read(PyObject *self, PyObject *args)
{
    int hid_fd = 0;
	int ret = 0;
    unsigned char reg_addr;
	unsigned char read_data;

    if (!PyArg_ParseTuple(args, "ib", &hid_fd, &reg_addr)) {
		PyErr_SetString(PyExc_RuntimeError, "Error parsing parameters");
		return (NULL);
	}

    ret = read_write_tigerjet(hid_fd, reg_addr, NULL, &read_data);
	if (ret != 0) {
		PyErr_SetString(PyExc_RuntimeError, "Error Reading TigerJet Register");
        return (NULL);
	}

	return (Py_BuildValue("B", read_data));
}

static PyObject *pytjapi_is_tigerjet(PyObject *self, PyObject *args)
{
	int hid_fd = 0;
	int ret = 0;

    if (!PyArg_ParseTuple(args, "i", &hid_fd)) {
		PyErr_SetString(PyExc_RuntimeError, "Error parsing parameters");
		return (NULL);
	}

    ret = is_tigerjet(hid_fd, NULL);
	if (ret == -1) {
		PyErr_SetString(PyExc_RuntimeError, "Error Reading Device's Vendor ID");
        return (NULL);
	}

	return (Py_BuildValue("O", ret ? Py_True : Py_False));
}


#if PY_MAJOR_VERSION >= 3

PyMODINIT_FUNC PyInit_pytjapi(void)
{
  PyObject *module = PyModule_Create(&module_def);
  if (module == NULL) {
    return (NULL);
  }

  return module;
}

#else

PyMODINIT_FUNC initpytjapi(void)
{
  PyObject *module = Py_InitModule3("pytjapi", module_methods, module_docstring);
  if (module == NULL) {
    return;
  }
}

#endif
