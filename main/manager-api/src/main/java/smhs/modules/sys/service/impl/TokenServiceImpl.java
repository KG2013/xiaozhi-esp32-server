package smhs.modules.sys.service.impl;

import org.springframework.stereotype.Service;

import lombok.AllArgsConstructor;
import smhs.modules.security.oauth2.TokenGenerator;
import smhs.modules.sys.service.TokenService;

@AllArgsConstructor
@Service
public class TokenServiceImpl implements TokenService {

    @Override
    public String createToken(long userId) {
        // 生成一个token
        String token = TokenGenerator.generateValue();
        return token;
    }
}
