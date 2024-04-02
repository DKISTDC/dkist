.. _dkist:index:

DKIST Python Tools Documentation
================================

The DKIST Python tools provide a package (`dkist`) which aims to help you search, obtain and use DKIST data as part of your Python software.
The `dkist` package is a `SunPy Affiliated Package <https://sunpy.org/affiliated>`__, meaning we integrate tightly with the rest of the SunPy ecosystem, making heavy use of the `sunpy` and `ndcube` packages.

.. toctree::
  :maxdepth: 1
  :hidden:

  self
  installation
  tutorial/index
  howto_guides/index
  topic_guides/index
  reference
  whatsnew/index
  developer


.. grid:: 2
    :gutter: 2

    .. grid-item-card:: Tutorial
        :link: dkist:tutorial:index
        :link-type: ref
        :text-align: center

        :material-outlined:`accessibility_new;8em;sd-text-secondary`

        This tutorial walks you through how to search for, download and load DKIST Level one data.

    .. grid-item-card:: How To Guides
        :link: dkist:howto-guides:index
        :link-type: ref
        :text-align: center

        :octicon:`question;8em;sd-text-secondary`

        Walkthroughs on how to achieve a specific task.

    .. grid-item-card:: Topic Guides
        :link: dkist:topic-guides:index
        :link-type: ref
        :text-align: center

        :material-outlined:`school;8em;sd-text-secondary`

        In-depth explanations of concepts and key topics.
        Most useful for answering "why" questions.

    .. grid-item-card:: Reference
        :link: dkist:api
        :link-type: ref
        :text-align: center

        :material-outlined:`code;8em;sd-text-secondary`

        Technical description of the inputs, outputs, and behavior of each component of the ``dkist`` package.

    .. grid-item-card:: Get Help
        :text-align: center

        :material-outlined:`live_help;8em;sd-text-secondary`

        .. button-link:: https://nso.atlassian.net/servicedesk/customer/portals
            :shadow:
            :expand:
            :color: primary

            **DKIST Help Desk**

        .. button-link:: https://app.element.io/#/room/#dki-solar-telescope:openastronomy.org
            :shadow:
            :expand:
            :color: primary

            **Join the chat**

        .. button-link:: https://github.com/sunpy/sunpy/issues
            :shadow:
            :expand:
            :color: primary

            **Report an issue**

        .. button-link:: https://community.openastronomy.org/c/sunpy/5
            :shadow:
            :expand:
            :color: primary

            **Post on Discourse**


What to Expect from the DKIST Python Tools
------------------------------------------

The `dkist` package is developed by the DKIST Data Center team, and it is designed to make it easy to obtain and use DKIST data in Python.
To achieve this goal the `dkist` package only provides DKIST specific functionality as plugins and extensions to the wider SunPy and scientific Python ecosystem.
This means that there isn't actually a lot of code in the `dkist` package, and most of the development effort required to support DKIST data happened in packages such as `ndcube`, `sunpy` and `astropy`.

The upshot of this when using the DKIST Python tools is that you will mostly not be (directly) using functionality provided by the `dkist` package.
You will need to be familiar with the other packages in the ecosystem to make use of the tools provided here.
The main interfaces you will need to know are `sunpy.net.Fido` and `ndcube.NDCube`, we cover these in :ref:`dkist:tutorial:index`.
