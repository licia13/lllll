function H = thwaites_H(lambda)

H   = ( 2.088 + 0.0731./( (-0.12)+0.14 ) ) .* ...
                                                        ( lambda <= -0.10 ) + ...
      ( 2.088 + 0.0731./( lambda+0.14 ) ) .* ...
                                       ( -0.10< lambda  & lambda <=  0.0 ) + ...
      ( 2.61 - 3.75 * lambda - 5.24 * lambda.^2 ) .* ...
                                       (  0.0 < lambda  & lambda <=  0.25 ) + ...
      ( 2.61 - 3.75 *   0.25  + 5.24 *    0.25^2 ) .* ...
                                                          ( 0.25 < lambda ) ;
