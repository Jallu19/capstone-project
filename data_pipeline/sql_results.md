# SQL Query Results

The project-defined conversion rate is `1 GBP = 105.50 INR`.

## select_where_order_limit
                                                                   title  price_inr
                                           Boar Island (Anna Pigeon #19)    6275.14
                                        A Year in Provence (Provence #1)    6000.84
                                                     The Past Never Ends    5960.75
                                        The Last Painting of Sara de Vos    5860.52
                                 A Flight of Arrows (The Pathfinders #2)    5858.42
                   Murder at the 42nd Street Library (Raymond Ambler #1)    5734.98
                                          The Last Mile (Amos Decker #2)    5719.16
                                                      Tipping the Velvet    5669.57
The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)    5517.65
                       The Guernsey Literary and Potato Peel Pie Society    5225.42

## distinct_categories
     category_name
Historical Fiction
           Mystery
            Travel

## price_between
                                                                                            title  price_gbp
                                                                             Love, Lies and Spies      20.55
                                                 Delivering the Truth (Quaker Midwife Mystery #1)      20.89
                                                                           Voyager (Outlander #3)      21.07
The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2)      23.21
                                What Happened on Beale Street (Secrets of the South Mysteries #2)      25.37
                                                               1,000 Places to See Before You Die      26.08
                                                                        Girl With a Pearl Earring      26.77
                                                                 Poisonous (Max Revere Novels #3)      26.80
                                                                                        The Widow      27.26
                                                                        The Marriage of Opposites      28.08

## in_clause
                                                                   title  rating
                                      1,000 Places to See Before You Die       5
                                  A Time of Torment (Charlie Parker #14)       5
       What Happened on Beale Street (Secrets of the South Mysteries #2)       5
The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)       5
      Full Moon over Noahâs Ark: An Odyssey to Mount Ararat and Beyond       4
                                        A Year in Provence (Provence #1)       4
                                                           Sharp Objects       4
                                                     The Past Never Ends       4
                         The Murder of Roger Ackroyd (Hercule Poirot #4)       4
                   Murder at the 42nd Street Library (Raymond Ambler #1)       4

## join_highest_rated
     category_name                                                                    title  rating  price_inr
Historical Fiction                                  A Flight of Arrows (The Pathfinders #2)       5    5858.42
Historical Fiction                                                             Mrs. Houdini       5    3191.38
Historical Fiction                                                    The Passion of Dolssa       5    2987.76
Historical Fiction                                                   Voyager (Outlander #3)       5    2222.89
Historical Fiction                                                             The Red Tent       5    3762.13
           Mystery                                   A Time of Torment (Charlie Parker #14)       5    5100.92
           Mystery        What Happened on Beale Street (Secrets of the South Mysteries #2)       5    2676.54
           Mystery The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)       5    5517.65
            Travel                                       1,000 Places to See Before You Die       5    2751.44
Historical Fiction                                                The Marriage of Opposites       4    2962.44
